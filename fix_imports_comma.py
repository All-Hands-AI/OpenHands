#!/usr/bin/env python3
import os
import re
import glob

# Find all run_infer.py files
run_infer_files = glob.glob('evaluation/benchmarks/*/run_infer.py')

# Process each file
for file_path in run_infer_files:
    print(f"Processing {file_path}...")
    
    # Read the file content
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Fix the extra comma
    if 'run_evaluation,,' in content:
        fixed_content = content.replace('run_evaluation,,', 'run_evaluation,')
        
        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.write(fixed_content)
        
        print(f"  Updated successfully")
    else:
        print(f"  No update needed")

print("Done!")