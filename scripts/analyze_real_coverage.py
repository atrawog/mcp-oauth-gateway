#!/usr/bin/env python3
"""Analyze real coverage data from the sidecar pattern."""

import sqlite3
import struct
from pathlib import Path
import json

def decode_line_bits(numbits_blob):
    """Decode the line bits from coverage.py's packed format."""
    covered_lines = set()
    if numbits_blob:
        # Each byte represents 8 lines
        for byte_idx, byte_val in enumerate(numbits_blob):
            if byte_val:
                base_line = byte_idx * 8
                for bit in range(8):
                    if byte_val & (1 << bit):
                        covered_lines.add(base_line + bit)
    return covered_lines

def analyze_coverage():
    """Extract and analyze coverage data."""
    coverage_db = Path(".coverage")
    if not coverage_db.exists():
        print("❌ No coverage database found!")
        return
    
    conn = sqlite3.connect(coverage_db)
    cursor = conn.cursor()
    
    print("📊 MCP OAuth Gateway - Real Coverage Analysis")
    print("=" * 80)
    
    # Get file coverage data
    cursor.execute("""
        SELECT f.id, f.path, l.numbits, c.context
        FROM file f
        JOIN line_bits l ON f.id = l.file_id
        LEFT JOIN context c ON l.context_id = c.id
        ORDER BY f.path
    """)
    
    file_coverage = {}
    for file_id, path, numbits, context in cursor.fetchall():
        if path not in file_coverage:
            file_coverage[path] = {
                'contexts': set(),
                'covered_lines': set(),
                'branches': 0
            }
        
        if context:
            file_coverage[path]['contexts'].add(context)
        
        # Decode line coverage
        lines = decode_line_bits(numbits)
        file_coverage[path]['covered_lines'].update(lines)
    
    # Get branch coverage
    cursor.execute("""
        SELECT f.path, COUNT(DISTINCT a.fromno || '-' || a.tono) as branch_count
        FROM file f
        JOIN arc a ON f.id = a.file_id
        GROUP BY f.path
    """)
    
    for path, branch_count in cursor.fetchall():
        if path in file_coverage:
            file_coverage[path]['branches'] = branch_count
    
    # Map paths and display results
    print("\n📁 Coverage by Module:")
    print("-" * 80)
    print(f"{'Module':<50} {'Lines':<12} {'Branches':<10} {'Contexts'}")
    print("-" * 80)
    
    total_lines = 0
    total_branches = 0
    
    for path, data in sorted(file_coverage.items()):
        # Map container path to module name
        module = path.split('/')[-1]
        lines_covered = len(data['covered_lines'])
        branches = data['branches']
        contexts = len(data['contexts'])
        
        total_lines += lines_covered
        total_branches += branches
        
        print(f"{module:<50} {lines_covered:<12} {branches:<10} {contexts}")
    
    print("-" * 80)
    print(f"{'TOTAL':<50} {total_lines:<12} {total_branches:<10}")
    
    # Show execution contexts
    print(f"\n🔄 Execution Contexts Found:")
    all_contexts = set()
    for data in file_coverage.values():
        all_contexts.update(data['contexts'])
    
    for ctx in sorted(all_contexts):
        if ctx:
            print(f"  - {ctx}")
    
    # Key module analysis
    print(f"\n🎯 Key Module Coverage:")
    print("-" * 80)
    
    key_modules = ['routes.py', 'auth_authlib.py', 'rfc7592.py', 'server.py']
    for module in key_modules:
        module_data = next((data for path, data in file_coverage.items() if path.endswith(module)), None)
        if module_data:
            print(f"\n✅ {module}:")
            print(f"   Lines executed: {len(module_data['covered_lines'])}")
            print(f"   Branch coverage: {module_data['branches']} branches")
            print(f"   Line numbers covered: {sorted(list(module_data['covered_lines']))[:20]}...")
    
    conn.close()
    
    print("\n✨ Real coverage analysis complete!")
    print(f"\n📈 Summary:")
    print(f"   Total lines executed: {total_lines}")
    print(f"   Total branches covered: {total_branches}")
    print(f"   Files with coverage: {len(file_coverage)}")

if __name__ == "__main__":
    analyze_coverage()