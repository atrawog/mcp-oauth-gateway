#!/usr/bin/env python3
"""Fix missing HTTP status code imports in test files."""

import re
from pathlib import Path


# All HTTP constants that might be used
HTTP_CONSTANTS = [
    "HTTP_OK", "HTTP_CREATED", "HTTP_ACCEPTED", "HTTP_NO_CONTENT",
    "HTTP_MOVED_PERMANENTLY", "HTTP_FOUND", "HTTP_SEE_OTHER",
    "HTTP_NOT_MODIFIED", "HTTP_TEMPORARY_REDIRECT", "HTTP_PERMANENT_REDIRECT",
    "HTTP_BAD_REQUEST", "HTTP_UNAUTHORIZED", "HTTP_FORBIDDEN",
    "HTTP_NOT_FOUND", "HTTP_METHOD_NOT_ALLOWED", "HTTP_NOT_ACCEPTABLE",
    "HTTP_CONFLICT", "HTTP_GONE", "HTTP_UNPROCESSABLE_ENTITY",
    "HTTP_TOO_MANY_REQUESTS", "HTTP_INTERNAL_SERVER_ERROR",
    "HTTP_NOT_IMPLEMENTED", "HTTP_BAD_GATEWAY", "HTTP_SERVICE_UNAVAILABLE",
    "HTTP_GATEWAY_TIMEOUT"
]

def find_missing_imports(file_path: Path):
    """Find which HTTP constants are used but not imported."""
    with open(file_path) as f:
        content = f.read()

    # Find all HTTP_ constants used in the file
    used_constants = set(re.findall(r'HTTP_[A-Z_]+', content))

    # Find all imported constants
    imported_constants = set()
    import_pattern = r'from \.test_constants import ([^\n]+)'
    for match in re.finditer(import_pattern, content):
        imports = match.group(1)
        # Handle multi-line imports
        for const in imports.split(','):
            const = const.strip()
            if const.startswith('HTTP_'):
                imported_constants.add(const)

    # Find single imports
    for const in HTTP_CONSTANTS:
        if f"import {const}" in content:
            imported_constants.add(const)

    # Find missing
    missing = used_constants - imported_constants
    return missing

def add_imports(file_path: Path, imports_to_add: set):
    """Add missing imports to a file."""
    if not imports_to_add:
        return False

    with open(file_path) as f:
        content = f.read()

    # Find the last import from test_constants
    import_pattern = r'(from \.test_constants import [^\n]+\n)'
    matches = list(re.finditer(import_pattern, content))

    if matches:
        # Add after the last test_constants import
        last_match = matches[-1]
        insert_pos = last_match.end()
        for import_name in sorted(imports_to_add):
            new_import = f"from .test_constants import {import_name}\n"
            content = content[:insert_pos] + new_import + content[insert_pos:]
            insert_pos += len(new_import)
    else:
        # Add at the beginning after other imports
        lines = content.split('\n')
        import_section_end = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith(('import ', 'from ')):
                import_section_end = i
                break

        new_imports = [f"from .test_constants import {name}" for name in sorted(imports_to_add)]
        lines[import_section_end:import_section_end] = new_imports
        content = '\n'.join(lines)

    with open(file_path, 'w') as f:
        f.write(content)

    return True

def main():
    """Fix missing imports in all test files."""
    print("Scanning for missing HTTP constant imports...\n")

    test_dir = Path("tests")
    fixed_files = []

    for test_file in test_dir.glob("test_*.py"):
        missing = find_missing_imports(test_file)
        if missing:
            print(f"{test_file.name}:")
            for const in sorted(missing):
                print(f"  ⚠️  Missing: {const}")

            if add_imports(test_file, missing):
                fixed_files.append(test_file.name)
                print("  ✅ Fixed!\n")

    if fixed_files:
        print(f"\n✅ Fixed {len(fixed_files)} files:")
        for file in sorted(fixed_files):
            print(f"  - {file}")
    else:
        print("✅ No missing imports found!")

if __name__ == "__main__":
    main()
