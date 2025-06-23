#!/usr/bin/env python3
import sys

import coverage


data_file = sys.argv[1] if len(sys.argv) > 1 else ".coverage"
cov = coverage.Coverage(data_file=data_file)
cov.load()

files = list(cov.get_data().measured_files())
print(f"Total files: {len(files)}")
print("\nFirst 10 files:")
for f in files[:10]:
    print(f"  {f}")
