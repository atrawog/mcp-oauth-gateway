#!/usr/bin/env python3
"""
Analyze test files to find which ones create client registrations
but don't clean them up using RFC 7592 DELETE endpoint.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple

def find_registration_patterns(content: str) -> List[Tuple[int, str]]:
    """Find lines that create client registrations"""
    patterns = [
        r'\.post\s*\(\s*["\'].*?/register',
        r'POST.*?/register',
        r'http_client\.post\s*\(\s*.*?/register',
        r'registered_client',  # Using the fixture
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
    """Find lines that clean up client registrations"""
    patterns = [
        r'\.delete\s*\(\s*["\'].*?/register',
        r'DELETE.*?/register',
        r'http_client\.delete\s*\(\s*.*?/register',
        r'cleanup.*client',
        r'teardown',
    ]
    
    results = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                results.append((i + 1, line.strip()))
                break
    return results

def analyze_test_files(test_dir: Path) -> Dict[str, Dict]:
    """Analyze all test files for registration and cleanup patterns"""
    results = {}
    
    for test_file in test_dir.glob("test*.py"):
        if test_file.name == "test_constants.py":
            continue
            
        with open(test_file, 'r') as f:
            content = f.read()
        
        registrations = find_registration_patterns(content)
        cleanups = find_cleanup_patterns(content)
        
        if registrations:  # Only include files that create registrations
            results[test_file.name] = {
                'registrations': registrations,
                'cleanups': cleanups,
                'has_cleanup': len(cleanups) > 0
            }
    
    return results

def main():
    test_dir = Path(__file__).parent.parent / "tests"
    results = analyze_test_files(test_dir)
    
    # Sort files by whether they have cleanup
    files_with_cleanup = []
    files_without_cleanup = []
    
    for filename, data in sorted(results.items()):
        if data['has_cleanup']:
            files_with_cleanup.append((filename, data))
        else:
            files_without_cleanup.append((filename, data))
    
    # Print results
    print("=" * 80)
    print("TEST FILES REGISTRATION CLEANUP ANALYSIS")
    print("=" * 80)
    
    print("\n✅ Files WITH proper cleanup:")
    print("-" * 40)
    for filename, data in files_with_cleanup:
        print(f"\n{filename}:")
        print(f"  Registrations: {len(data['registrations'])} occurrences")
        print(f"  Cleanups: {len(data['cleanups'])} occurrences")
        if len(data['registrations']) > 0:
            print(f"  First registration at line {data['registrations'][0][0]}")
        if len(data['cleanups']) > 0:
            print(f"  First cleanup at line {data['cleanups'][0][0]}")
    
    print("\n\n❌ Files WITHOUT proper cleanup:")
    print("-" * 40)
    for filename, data in files_without_cleanup:
        print(f"\n{filename}:")
        print(f"  Registrations: {len(data['registrations'])} occurrences")
        for line_no, line in data['registrations'][:3]:  # Show first 3
            print(f"    Line {line_no}: {line[:80]}...")
    
    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total test files analyzed: {len(results)}")
    print(f"Files with cleanup: {len(files_with_cleanup)}")
    print(f"Files WITHOUT cleanup: {len(files_without_cleanup)}")
    
    if files_without_cleanup:
        print("\n⚠️  ACTION REQUIRED:")
        print("The following files create client registrations but don't clean them up:")
        for filename, _ in files_without_cleanup:
            print(f"  - {filename}")
        print("\nThese files should use the RFC 7592 DELETE endpoint to clean up registrations!")

if __name__ == "__main__":
    main()