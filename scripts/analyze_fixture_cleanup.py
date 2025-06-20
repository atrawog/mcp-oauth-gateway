#!/usr/bin/env python3
"""
Analyze test files that use the registered_client fixture
to see if they clean up the registrations properly.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set

def find_registered_client_usage(content: str) -> List[Tuple[int, str]]:
    """Find lines that use registered_client fixture"""
    patterns = [
        r'registered_client\s*[,\)]',  # As function parameter
        r'registered_client\[',  # Accessing client properties
    ]
    
    results = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line):
                results.append((i + 1, line.strip()))
                break
    return results

def find_direct_registrations(content: str) -> List[Tuple[int, str]]:
    """Find lines that directly POST to /register"""
    patterns = [
        r'\.post\s*\(\s*[^,]*?/register["\']',
        r'POST.*?/register(?:["\']|\s)',
    ]
    
    results = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                results.append((i + 1, line.strip()))
                break
    return results

def find_cleanup_patterns(content: str) -> List[Tuple[int, str]]:
    """Find lines that clean up client registrations via RFC 7592"""
    patterns = [
        r'\.delete\s*\(\s*[^,]*?/register/[^/\s]+["\']',  # DELETE /register/{client_id}
        r'DELETE.*?/register/[^/\s]+',
    ]
    
    results = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                results.append((i + 1, line.strip()))
                break
    return results

def analyze_test_file(filepath: Path) -> Dict:
    """Analyze a single test file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    fixture_usage = find_registered_client_usage(content)
    direct_registrations = find_direct_registrations(content)
    cleanups = find_cleanup_patterns(content)
    
    # Count test functions
    test_functions = len(re.findall(r'async def test_\w+', content))
    
    return {
        'fixture_usage': fixture_usage,
        'direct_registrations': direct_registrations,
        'cleanups': cleanups,
        'test_functions': test_functions,
        'has_registrations': len(fixture_usage) > 0 or len(direct_registrations) > 0,
        'has_cleanup': len(cleanups) > 0
    }

def main():
    test_dir = Path(__file__).parent.parent / "tests"
    
    # Files we know do proper cleanup
    known_good_files = {
        'test_rfc7592_compliance.py',
        'test_rfc7592_security.py', 
        'test_eternal_client.py',
        'test_mcp_client_rfc7592.py'
    }
    
    results = {}
    
    for test_file in sorted(test_dir.glob("test*.py")):
        if test_file.name == "test_constants.py" or test_file.name == "conftest.py":
            continue
            
        analysis = analyze_test_file(test_file)
        if analysis['has_registrations']:  # Only include files that create registrations
            results[test_file.name] = analysis
    
    # Categorize files
    fixture_without_cleanup = []
    direct_with_cleanup = []
    direct_without_cleanup = []
    
    for filename, data in results.items():
        if filename in known_good_files:
            direct_with_cleanup.append((filename, data))
        elif data['fixture_usage'] and not data['has_cleanup']:
            fixture_without_cleanup.append((filename, data))
        elif data['direct_registrations'] and data['has_cleanup']:
            direct_with_cleanup.append((filename, data))
        elif data['direct_registrations'] and not data['has_cleanup']:
            direct_without_cleanup.append((filename, data))
    
    # Print results
    print("=" * 80)
    print("CLIENT REGISTRATION CLEANUP ANALYSIS")
    print("=" * 80)
    
    print("\n✅ Files that create registrations WITH proper cleanup:")
    print("-" * 40)
    for filename, data in sorted(direct_with_cleanup):
        print(f"\n{filename}:")
        print(f"  Direct registrations: {len(data['direct_registrations'])}")
        print(f"  Cleanup calls: {len(data['cleanups'])}")
        print(f"  Test functions: {data['test_functions']}")
    
    print("\n\n❌ Files using registered_client fixture WITHOUT cleanup:")
    print("-" * 40)
    for filename, data in sorted(fixture_without_cleanup):
        print(f"\n{filename}:")
        print(f"  Fixture usage: {len(data['fixture_usage'])} occurrences")
        print(f"  Test functions: {data['test_functions']}")
        if data['fixture_usage']:
            print(f"  First usage at line {data['fixture_usage'][0][0]}")
    
    print("\n\n❌ Files with direct registrations WITHOUT cleanup:")
    print("-" * 40)
    for filename, data in sorted(direct_without_cleanup):
        print(f"\n{filename}:")
        print(f"  Direct registrations: {len(data['direct_registrations'])}")
        print(f"  Test functions: {data['test_functions']}")
        if data['direct_registrations']:
            print(f"  First registration at line {data['direct_registrations'][0][0]}")
    
    # Summary and recommendations
    print("\n\n" + "=" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    
    total_without_cleanup = len(fixture_without_cleanup) + len(direct_without_cleanup)
    print(f"\nTotal files creating registrations: {len(results)}")
    print(f"Files with proper cleanup: {len(direct_with_cleanup)}")
    print(f"Files WITHOUT cleanup: {total_without_cleanup}")
    
    if fixture_without_cleanup:
        print("\n🔧 RECOMMENDATION 1: Fix the registered_client fixture")
        print("The registered_client fixture in conftest.py should be updated to include")
        print("automatic cleanup using pytest's fixture finalization:")
        print("\n@pytest.fixture")
        print("async def registered_client(http_client, wait_for_services):")
        print("    # ... existing registration code ...")
        print("    yield client_data")
        print("    # Cleanup: Use RFC 7592 DELETE")
        print("    if 'registration_access_token' in client_data:")
        print("        await http_client.delete(")
        print("            f\"{AUTH_BASE_URL}/register/{client_data['client_id']}\",")
        print("            headers={'Authorization': f\"Bearer {client_data['registration_access_token']}\"}") 
        print("        )")
    
    if direct_without_cleanup:
        print("\n🔧 RECOMMENDATION 2: Add cleanup to direct registration tests")
        print("Tests that directly call POST /register should add cleanup:")
        print("- Use try/finally blocks")
        print("- Or use pytest fixtures with yield for automatic cleanup")
        print("- Call DELETE /register/{client_id} with registration_access_token")

if __name__ == "__main__":
    main()