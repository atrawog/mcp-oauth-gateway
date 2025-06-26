#!/usr/bin/env python3
"""Fix coverage paths and generate detailed report with actual metrics."""

import sqlite3
from pathlib import Path


def extract_coverage_data():
    """Extract actual coverage data from the database."""
    coverage_db = Path(".coverage")
    if not coverage_db.exists():
        print("❌ No coverage database found!")
        return None

    conn = sqlite3.connect(coverage_db)
    cursor = conn.cursor()

    # Get all files and their coverage data
    cursor.execute("""
        SELECT f.path,
               COUNT(DISTINCT l.lineno) as lines_covered,
               GROUP_CONCAT(DISTINCT l.lineno) as covered_lines
        FROM file f
        JOIN line_bits l ON f.id = l.file_id
        GROUP BY f.path
    """)

    coverage_data = {}
    for path, lines_covered, covered_lines in cursor.fetchall():
        coverage_data[path] = {
            "lines_covered": lines_covered,
            "covered_lines": set(map(int, covered_lines.split(","))) if covered_lines else set(),
        }

    # Get arc data if available
    cursor.execute("""
        SELECT f.path,
               COUNT(DISTINCT a.fromno || '-' || a.tono) as branches_covered
        FROM file f
        JOIN arc a ON f.id = a.file_id
        GROUP BY f.path
    """)

    for path, branches_covered in cursor.fetchall():
        if path in coverage_data:
            coverage_data[path]["branches_covered"] = branches_covered

    conn.close()
    return coverage_data


def map_and_analyze_coverage():
    """Map coverage to local files and calculate percentages."""
    coverage_data = extract_coverage_data()
    if not coverage_data:
        return None

    # Path mappings
    path_map = {
        "/usr/local/lib/python3.11/site-packages/mcp_oauth_dynamicclient/": "mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/"
    }

    results = []
    total_lines_covered = 0

    for container_path, data in coverage_data.items():
        # Map to local path
        local_path = container_path
        for prefix, replacement in path_map.items():
            if container_path.startswith(prefix):
                local_path = container_path.replace(prefix, replacement)
                break

        # Try to count total lines in local file
        local_file = Path(local_path)
        total_lines = 0
        if local_file.exists():
            try:
                with open(local_file) as f:
                    total_lines = len(f.readlines())
            except:
                pass

        coverage_pct = (data["lines_covered"] / total_lines * 100) if total_lines > 0 else 0
        total_lines_covered += data["lines_covered"]

        results.append(
            {
                "file": local_path.replace("mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/", ""),
                "lines_covered": data["lines_covered"],
                "total_lines": total_lines,
                "coverage_pct": coverage_pct,
                "branches_covered": data.get("branches_covered", 0),
            }
        )

    return results, total_lines_covered


def generate_detailed_report():
    """Generate a detailed coverage report."""
    print("📊 MCP OAuth Gateway - Detailed Coverage Report")
    print("=" * 80)

    results, total_lines = map_and_analyze_coverage()
    if not results:
        print("❌ No coverage data found!")
        return

    print("\n📈 Coverage Summary:")
    print(f"   Total lines executed: {total_lines}")
    print(f"   Files covered: {len(results)}")

    print("\n📁 File Coverage Details:")
    print("-" * 80)
    print(f"{'File':<40} {'Lines':<15} {'Coverage':<10} {'Branches'}")
    print("-" * 80)

    # Sort by coverage percentage
    results.sort(key=lambda x: x["coverage_pct"], reverse=True)

    for result in results:
        file_name = result["file"]
        if len(file_name) > 39:
            file_name = "..." + file_name[-36:]

        lines_info = f"{result['lines_covered']}/{result['total_lines']}"
        coverage = f"{result['coverage_pct']:.1f}%" if result["total_lines"] > 0 else "N/A"
        branches = result["branches_covered"]

        print(f"{file_name:<40} {lines_info:<15} {coverage:<10} {branches}")

    # Calculate module-specific coverage
    print("\n🔍 Module-Specific Analysis:")
    print("-" * 80)

    key_modules = {
        "routes.py": "OAuth Routes & Endpoints",
        "auth_authlib.py": "Authentication & Authorization",
        "rfc7592.py": "RFC 7592 Client Management",
        "async_resource_protector.py": "Bearer Token Protection",
        "server.py": "FastAPI Server",
        "redis_client.py": "Redis Storage",
        "keys.py": "JWT Key Management",
    }

    for module, description in key_modules.items():
        module_data = next((r for r in results if r["file"] == module), None)
        if module_data:
            print(f"✅ {description} ({module}):")
            print(f"   Lines covered: {module_data['lines_covered']}")
            print(f"   Total lines: {module_data['total_lines']}")
            print(f"   Coverage: {module_data['coverage_pct']:.1f}%")
            print(f"   Branches: {module_data['branches_covered']}")
            print()

    print("\n✨ Coverage report complete!")


if __name__ == "__main__":
    generate_detailed_report()
