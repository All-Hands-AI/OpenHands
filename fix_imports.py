#!/usr/bin/env python3
import os
import re
import glob

# Find all run_infer.py files
run_infer_files = glob.glob('evaluation/benchmarks/*/run_infer.py')

# Pattern to match: from evaluation.utils.shared import ... without update_agent_config_for_eval
pattern1 = r'from evaluation\.utils\.shared import \((.*?)\)'
# Pattern to match: agent_config = config.get_agent_config(metadata.agent_class)
pattern2 = r'(agent_config\s*=\s*config\.get_agent_config\([^)]*\))\s*from evaluation\.utils\.shared import update_agent_config_for_eval\s*agent_config = update_agent_config_for_eval\(agent_config\)'

# Process each file
for file_path in run_infer_files:
    print(f"Processing {file_path}...")
    
    # Read the file content
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Fix the import statement
    if 'update_agent_config_for_eval' not in content:
        # Skip files that don't need fixing
        continue
    
    # Fix the inline import and function call
    if 'from evaluation.utils.shared import update_agent_config_for_eval\nagent_config = update_agent_config_for_eval(agent_config)' in content:
        # Move the import to the top
        # First, extract the current imports
        import_match = re.search(pattern1, content, re.DOTALL)
        if import_match:
            imports = import_match.group(1).strip()
            # Add update_agent_config_for_eval if not already there
            if 'update_agent_config_for_eval' not in imports:
                new_imports = imports + ',\n    update_agent_config_for_eval,'
                new_import_block = f'from evaluation.utils.shared import (\n{new_imports}\n)'
                content = re.sub(pattern1, new_import_block, content, flags=re.DOTALL)
        
        # Fix the function call
        content = re.sub(
            pattern2, 
            r'\1\nagent_config = update_agent_config_for_eval(agent_config)', 
            content
        )
    
    # Write the updated content back to the file
    with open(file_path, 'w') as file:
        file.write(content)
    
    print(f"  Updated successfully")

print("Done!")