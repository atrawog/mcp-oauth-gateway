#!/usr/bin/env python3
"""
Generate coverage report from sidecar coverage data.
Maps installed package paths to source code paths.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Generate coverage report with proper path mapping."""
    # Ensure we're in the right directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check if coverage data exists
    coverage_file = project_root / ".coverage"
    if not coverage_file.exists():
        print("❌ No coverage data found. Run 'just test-sidecar-coverage' first.")
        sys.exit(1)
    
    # Create a temporary .coveragerc with proper path mappings
    coveragerc_content = """[paths]
# Map installed package paths to source code
source =
    /usr/local/lib/python3.11/site-packages/mcp_oauth_dynamicclient
    /usr/local/lib/python*/site-packages/mcp_oauth_dynamicclient
    mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient
    ./mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient

[report]
precision = 2
show_missing = True
skip_empty = True

[html]
directory = htmlcov
"""
    
    temp_coveragerc = project_root / ".coveragerc.temp"
    with open(temp_coveragerc, "w") as f:
        f.write(coveragerc_content)
    
    try:
        # Set COVERAGE_FILE environment variable
        env = os.environ.copy()
        env["COVERAGE_FILE"] = str(coverage_file)
        
        # Combine coverage data (in case there are multiple files)
        print("🔄 Combining coverage data...")
        subprocess.run(
            ["coverage", "combine", f"--rcfile={temp_coveragerc}"],
            env=env,
            check=False  # Don't fail if already combined
        )
        
        # First, check if source files exist locally
        source_dir = project_root / "mcp-oauth-dynamicclient" / "src" / "mcp_oauth_dynamicclient"
        if not source_dir.exists():
            print(f"❌ Source directory not found: {source_dir}")
            print("   Make sure mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient exists")
            sys.exit(1)
        
        # Generate text report
        print("\n📊 Coverage Report:")
        print("=" * 80)
        result = subprocess.run(
            ["coverage", "report", f"--rcfile={temp_coveragerc}", "--skip-covered", "--skip-empty"],
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 and "No source for code" in result.stderr:
            print("⚠️  Coverage data contains container paths. Attempting to remap...")
            # Try mapping with source filter
            result = subprocess.run(
                ["coverage", "report", f"--rcfile={temp_coveragerc}", 
                 "--include=mcp-oauth-dynamicclient/src/*",
                 "--omit=*/tests/*,*/test_*",
                 "--skip-covered", "--skip-empty"],
                env=env,
                capture_output=True,
                text=True
            )
        
        if result.stdout:
            print(result.stdout)
        elif result.stderr:
            print(f"⚠️  No coverage data could be mapped to local sources")
            print(f"Debug info: {result.stderr[:200]}...")
        
        # Generate HTML report
        print("\n🌐 Generating HTML report...")
        result = subprocess.run(
            ["coverage", "html", f"--rcfile={temp_coveragerc}", "--ignore-errors"],
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ HTML report generated in htmlcov/")
        else:
            print(f"⚠️  HTML generation had issues: {result.stderr}")
        
    finally:
        # Clean up temporary file
        if temp_coveragerc.exists():
            temp_coveragerc.unlink()
    
    print("\n✨ Coverage report generation complete!")

if __name__ == "__main__":
    main()