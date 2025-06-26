#!/usr/bin/env python3
"""Generate coverage report from sidecar coverage data."""

import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path


def fix_coverage_paths():
    """Fix paths in coverage database to match local source."""
    coverage_db = Path(".coverage")
    if not coverage_db.exists():
        return

    print("🔧 Fixing coverage paths...")

    # Connect to the coverage database
    conn = sqlite3.connect(coverage_db)
    cursor = conn.cursor()

    # Get all files
    cursor.execute("SELECT id, path FROM file")
    files = cursor.fetchall()

    # Path mappings
    mappings = {
        "/usr/local/lib/python3.11/site-packages/mcp_oauth_dynamicclient/": "mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/",
        "/src/mcp_oauth_dynamicclient/": "mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/",
        "/app/mcp_oauth_dynamicclient/": "mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/",
        "/workspace/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/": "mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/",
    }

    # Update paths and remove auth.py
    updated = 0
    removed = 0
    for file_id, path in files:
        # Skip auth.py files
        if path.endswith("/auth.py"):
            cursor.execute("DELETE FROM file WHERE id = ?", (file_id,))
            cursor.execute("DELETE FROM line_bits WHERE file_id = ?", (file_id,))
            cursor.execute("DELETE FROM arc WHERE file_id = ?", (file_id,))
            cursor.execute("DELETE FROM tracer WHERE file_id = ?", (file_id,))
            print(f"  Removed: {path}")
            removed += 1
            continue

        new_path = path
        for old_prefix, new_prefix in mappings.items():
            if path.startswith(old_prefix):
                new_path = path.replace(old_prefix, new_prefix)
                break

        if new_path != path:
            cursor.execute("UPDATE file SET path = ? WHERE id = ?", (new_path, file_id))
            print(f"  Updated: {path} -> {new_path}")
            updated += 1

    conn.commit()
    conn.close()
    print(f"  Fixed {updated} file paths, removed {removed} auth.py files")


def main():
    """Generate coverage report from collected data."""
    # Copy coverage files from htmlcov if they exist
    htmlcov_dir = Path("htmlcov")
    if htmlcov_dir.exists():
        for coverage_file in htmlcov_dir.glob(".coverage*"):
            target = Path(coverage_file.name)
            if not target.exists():
                shutil.copy2(coverage_file, target)
                print(f"Copied {coverage_file} to {target}")

    # Look for coverage files in current directory
    coverage_files = list(Path(".").glob(".coverage*"))

    if not coverage_files:
        print("❌ No coverage files found!")
        print("Make sure to run 'just test-sidecar-coverage' first.")
        return 1

    print(f"Found {len(coverage_files)} coverage file(s)")

    # Combine coverage data
    print("\n🔄 Combining coverage data...")
    result = subprocess.run(["coverage", "combine", "--keep"], check=False, capture_output=True, text=True)

    if result.returncode != 0 and "No data to combine" not in result.stderr:
        print(f"❌ Error combining coverage data: {result.stderr}")

    # Fix paths in the combined database
    fix_coverage_paths()

    # Generate text report
    print("\n📊 Coverage Report:")
    print("=" * 80)
    result = subprocess.run(
        ["coverage", "report", "--show-missing", "--omit=*/auth.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and result.stdout:
        print(result.stdout)
    else:
        print(f"⚠️  Report generation had issues: {result.stderr}")

    # Generate HTML report
    print("\n🌐 Generating HTML report...")
    result = subprocess.run(
        ["coverage", "html", "--show-contexts"],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ HTML report generated in htmlcov/")
    else:
        print(f"⚠️  HTML generation had issues: {result.stderr}")

    print("\n✨ Coverage report generation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
