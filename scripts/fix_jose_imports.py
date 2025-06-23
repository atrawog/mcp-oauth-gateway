#!/usr/bin/env python3
"""Fix jose imports in test files by removing them
Most tests don't actually use JWT directly.
"""
import os
import re


# Find all test files that import jose
test_dir = "tests"
for filename in os.listdir(test_dir):
    if filename.endswith(".py"):
        filepath = os.path.join(test_dir, filename)

        with open(filepath) as f:
            content = f.read()

        original_content = content

        # Remove jose imports
        content = re.sub(r'^from jose import.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^import jose.*$', '', content, flags=re.MULTILINE)

        # Clean up double blank lines
        content = re.sub(r'\n\n\n+', '\n\n', content)

        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"Fixed imports in {filename}")
