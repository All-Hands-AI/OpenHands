#!/usr/bin/env python3
import os
import re
import glob

# Find all run_infer.py files
run_infer_files = glob.glob('evaluation/benchmarks/*/run_infer.py')

# Pattern to match: agent_config = config.get_agent_config(metadata.agent_class)
pattern = r'(agent_config\s*=\s*config\.get_agent_config\([^)]*\))'

# Replacement: add update_agent_config_for_eval
replacement = r'\1\nfrom evaluation.utils.shared import update_agent_config_for_eval\nagent_config = update_agent_config_for_eval(agent_config)'

# Process each file
for file_path in run_infer_files:
    print(f"Processing {file_path}...")
    
    # Read the file content
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Check if the file already imports update_agent_config_for_eval
    if 'update_agent_config_for_eval' in content:
        print(f"  Already updated, skipping")
        continue
    
    # Apply the replacement
    updated_content = re.sub(pattern, replacement, content)
    
    # Write the updated content back to the file
    if updated_content != content:
        with open(file_path, 'w') as file:
            file.write(updated_content)
        print(f"  Updated successfully")
    else:
        print(f"  No matching pattern found")

print("Done!")