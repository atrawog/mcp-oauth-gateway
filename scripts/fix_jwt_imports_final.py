#!/usr/bin/env python3
"""Final fix for JWT imports in test files."""
import os


# Find all test files that have the broken import
test_dir = "tests"
files_to_fix = []

for filename in os.listdir(test_dir):
    if filename.endswith(".py") and filename != "jwt_test_helper.py":
        filepath = os.path.join(test_dir, filename)

        with open(filepath) as f:
            content = f.read()

        # Check if file has the broken import pattern
        if "from .jwt_test_helper import encode as jwt_encode" in content:
            files_to_fix.append((filepath, content))

# Fix each file
for filepath, content in files_to_fix:
    # Fix the broken import pattern
    lines = content.split('\n')
    fixed_lines = []

    for _i, line in enumerate(lines):
        if line.strip() == "from .jwt_test_helper import encode as jwt_encode":
            # This import is on its own line, good
            fixed_lines.append(line)
        elif "from .jwt_test_helper import encode as jwt_encode" in line:
            # The import got mixed with other imports, fix it
            # Extract the other imports
            before = line[:line.index("from .jwt_test_helper")]
            after = line[line.index("from .jwt_test_helper"):]

            if before.strip().startswith("from .test_constants import"):
                # Add jwt import on next line
                fixed_lines.append("from .jwt_test_helper import encode as jwt_encode")
                fixed_lines.append(before.strip())
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    # Write back
    with open(filepath, 'w') as f:
        f.write('\n'.join(fixed_lines))
    print(f"Fixed imports in {os.path.basename(filepath)}")
