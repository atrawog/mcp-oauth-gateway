#!/usr/bin/env python3
"""Fix JWT imports in test files to use our test helper."""
import os
import re


# Find all test files that use jwt.encode
test_dir = "tests"
files_to_fix = []

for filename in os.listdir(test_dir):
    if filename.endswith(".py") and filename != "jwt_test_helper.py":
        filepath = os.path.join(test_dir, filename)

        with open(filepath) as f:
            content = f.read()

        if "jwt.encode" in content:
            files_to_fix.append((filepath, content))

# Fix each file
for filepath, content in files_to_fix:
    original_content = content

    # Add import if file uses jwt.encode
    if "jwt.encode" in content and "from .jwt_test_helper import" not in content:
        # Find where to add the import (after other imports)
        import_section_end = 0
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith(('import ', 'from ')):
                import_section_end = i + 1
            elif import_section_end > 0 and line and not line.startswith(' ') and not line.startswith('#'):
                break

        # Add the import
        lines.insert(import_section_end, "from .jwt_test_helper import encode as jwt_encode")
        content = '\n'.join(lines)

        # Replace jwt.encode with jwt_encode
        content = re.sub(r'jwt\.encode\(', 'jwt_encode(', content)

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed JWT usage in {os.path.basename(filepath)}")
