#!/usr/bin/env python3
"""Extract actual coverage metrics from the database."""

import sqlite3
from pathlib import Path


def count_set_bits(blob):
    """Count the number of set bits in a blob."""
    if not blob:
        return 0
    count = 0
    for byte in blob:
        count += bin(byte).count('1')
    return count

def extract_coverage():
    """Extract coverage data and generate report."""
    db_path = Path(".coverage")
    if not db_path.exists():
        print("No coverage database found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all files with coverage data
    cursor.execute("""
        SELECT f.path, l.numbits
        FROM file f
        JOIN line_bits l ON f.id = l.file_id
    """)

    coverage_data = {}
    for path, numbits in cursor.fetchall():
        if path not in coverage_data:
            coverage_data[path] = 0
        coverage_data[path] += count_set_bits(numbits)

    # Also get arc data
    cursor.execute("""
        SELECT f.path, COUNT(*) as arcs
        FROM file f
        JOIN arc a ON f.id = a.file_id
        GROUP BY f.path
    """)

    arc_data = {}
    for path, arcs in cursor.fetchall():
        arc_data[path] = arcs

    conn.close()

    # Generate report
    print("📊 MCP OAuth Gateway - ACTUAL Coverage Report")
    print("=" * 80)
    print(f"{'Module':<60} {'Lines':<10} {'Branches'}")
    print("-" * 80)

    total_lines = 0
    total_branches = 0

    for path, lines in sorted(coverage_data.items()):
        module = path.split('/')[-1]
        branches = arc_data.get(path, 0)
        total_lines += lines
        total_branches += branches
        print(f"{module:<60} {lines:<10} {branches}")

    print("-" * 80)
    print(f"{'TOTAL':<60} {total_lines:<10} {total_branches}")
    print()
    print(f"✅ Coverage data successfully collected from {len(coverage_data)} modules")
    print(f"📈 Total lines executed: {total_lines}")
    print(f"🌿 Total branches covered: {total_branches}")

if __name__ == "__main__":
    extract_coverage()
