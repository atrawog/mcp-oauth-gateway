#!/usr/bin/env python3
"""Ensure all tests use unique client IDs for parallel execution."""

import re
from pathlib import Path


def create_unique_fixtures():
    """Create fixtures for unique client identification."""
    return '''
# Add these fixtures to conftest.py for parallel-safe client registration

import uuid
import time
from datetime import datetime

@pytest.fixture
def worker_id(request):
    """Return the current pytest-xdist worker ID.
    Returns 'master' if not running in parallel mode.
    Returns 'gw0', 'gw1', etc. when running with pytest-xdist.
    """
    return os.environ.get('PYTEST_XDIST_WORKER', 'master')


@pytest.fixture
def unique_test_id(request, worker_id):
    """Generate a unique test identifier including worker ID.
    Format: {worker_id}_{timestamp}_{uuid}_{test_name}
    """
    test_name = request.node.name.replace('[', '_').replace(']', '_').replace(' ', '_')
    timestamp = int(time.time() * 1000)  # Millisecond precision
    unique_part = str(uuid.uuid4())[:8]
    return f"{worker_id}_{timestamp}_{unique_part}_{test_name}"


@pytest.fixture
def unique_client_name(unique_test_id):
    """Generate a guaranteed unique client name for OAuth registration.
    This ensures no conflicts between parallel test workers.
    """
    # Keep the TEST prefix for consistency with existing patterns
    return f"TEST {unique_test_id}"


@pytest.fixture
async def registered_client(http_client: httpx.AsyncClient, unique_client_name):
    """Create and register a test OAuth client with automatic cleanup.
    Each test gets its own unique client to prevent parallel conflicts.
    """
    # Register client with unique name
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": [TEST_OAUTH_CALLBACK_URL],
            "client_name": unique_client_name,
            "scope": TEST_CLIENT_SCOPE,
        },
        timeout=TEST_HTTP_TIMEOUT,
    )
    assert response.status_code == 201
    client_data = response.json()

    # Store the registration access token for cleanup
    registration_token = client_data.get("registration_access_token")

    yield client_data

    # Cleanup: Delete the client using RFC 7592
    if registration_token and "registration_client_uri" in client_data:
        try:
            delete_response = await http_client.delete(
                client_data["registration_client_uri"],
                headers={"Authorization": f"Bearer {registration_token}"},
                timeout=TEST_HTTP_TIMEOUT,
            )
            # 204 No Content is expected for successful deletion
            assert delete_response.status_code in (204, 404)
        except Exception as e:
            # Log but don't fail the test if cleanup fails
            print(f"Warning: Failed to cleanup client {client_data['client_id']}: {e}")
'''


def update_hardcoded_client_names():
    """Find and update tests with hardcoded client names."""
    updates_needed = []
    test_dir = Path("tests")

    # Patterns to find hardcoded client names
    patterns = [
        # Direct string literals
        (r'"TEST test_[^"]*"', "Uses hardcoded client name"),
        (r"'TEST test_[^']*'", "Uses hardcoded client name"),
        # client_name in JSON
        ('"client_name":' + "\\s*" + '"TEST [^"]*"', "Hardcoded client_name in JSON"),
        # Fixed test-client references
        (r'["\'"]test-client["\'"]', "Uses fixed test-client name"),
    ]

    for test_file in test_dir.glob("test_*.py"):
        content = test_file.read_text()

        for pattern, description in patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Check if it's already using a fixture
                if "unique_client_name" not in content and "registered_client" not in content:
                    updates_needed.append({"file": test_file.name, "matches": matches, "description": description})

    return updates_needed


def generate_update_script(updates_needed):
    """Generate a script to update tests with unique client names."""
    # Convert updates_needed to a string representation
    updates_str = repr(updates_needed)

    script = f'''#!/usr/bin/env python3
"""Update tests to use unique client names for parallel execution."""

import re
from pathlib import Path

def update_test_file(filepath, test_name_in_string=None):
    """Update a test file to use unique_client_name fixture."""
    content = filepath.read_text()

    # Check if the test function already has unique_client_name parameter
    # Use double escaping for Python 3.13 compatibility
    pattern = r'(?:async )?def (test_[a-zA-Z0-9_]+)' + '\\\\(' + '[^)]*' + '\\\\)' + ':'
    test_functions = re.findall(pattern, content)

    for func_name in test_functions:
        # Find the function definition
        func_pattern = rf'((?:async )?def {{func_name}})' + '\\\\(' + ')([^)]*)' + '\\\\)' + ':'
        match = re.search(func_pattern, content)

        if match and test_name_in_string and func_name in test_name_in_string:
            params = match.group(2)

            # Add unique_client_name if not present
            if 'unique_client_name' not in params:
                if params.strip():
                    new_params = params + ', unique_client_name'
                else:
                    new_params = 'unique_client_name'

                content = content.replace(
                    match.group(0),
                    f'{{match.group(1)}}{{new_params}}):'
                )

            # Replace hardcoded client names with fixture
            content = re.sub(
                rf'"TEST {{func_name}}"',
                'unique_client_name',
                content
            )
            content = re.sub(
                rf"'TEST {{func_name}}'",
                'unique_client_name',
                content
            )

    # Update client_name in JSON objects
    content = re.sub(
        '"client_name":' + '\\\\s*' + '"TEST [^"]*"',
        '"client_name": unique_client_name',
        content
    )

    filepath.write_text(content)
    print(f"✅ Updated {{filepath}}")


# Apply updates to specific files
updates = {updates_str}

for update in updates:
    filepath = Path("tests") / update['file']
    update_test_file(filepath, update.get('test_name'))
'''

    return script


def main():
    print("🔍 Analyzing test files for client ID uniqueness...")
    print("=" * 60)

    # Check for hardcoded client names
    updates_needed = update_hardcoded_client_names()

    if updates_needed:
        print("\n⚠️  Found tests with hardcoded client names:")
        for update in updates_needed:
            print(f"\n📄 {update['file']}:")
            print(f"   {update['description']}")
            for match in update["matches"][:3]:  # Show first 3 matches
                print(f"   - {match}")
            if len(update["matches"]) > 3:
                print(f"   ... and {len(update['matches']) - 3} more")

        # Generate update script
        script = generate_update_script(updates_needed)
        script_path = Path("scripts/apply_unique_client_updates.py")
        script_path.write_text(script)
        script_path.chmod(0o755)

        print(f"\n📝 Generated update script: {script_path}")
        print("   Run it with: python scripts/apply_unique_client_updates.py")
    else:
        print("\n✅ All tests appear to use dynamic client registration!")

    print("\n📋 Next Steps for Parallel Test Execution:")
    print("1. Add unique client fixtures to conftest.py")
    print("2. Update any tests with hardcoded names")
    print("3. Run tests with: just test -n auto")

    print("\n🎯 Parallel Execution Commands:")
    print("   just test -n auto              # Use all CPU cores")
    print("   just test -n 4                 # Use 4 workers")
    print("   just test -n 4 --dist loadscope # Group by test class")
    print("   just test -n auto -x           # Stop on first failure")

    # Write the fixture code
    fixture_path = Path("scripts/parallel_client_fixtures.py")
    fixture_path.write_text(create_unique_fixtures())
    print(f"\n✅ Created fixture code at: {fixture_path}")


if __name__ == "__main__":
    main()
