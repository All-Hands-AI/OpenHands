#!/usr/bin/env python3
import os
import re
import glob

# Find all run_infer.py files
run_infer_files = glob.glob('evaluation/benchmarks/*/run_infer.py')

# Pattern to match: agent_config = update_agent_config_for_eval(agent_config) with wrong indentation
pattern = r'(\s+)agent_config = config\.get_agent_config\([^)]*\)\s*agent_config = update_agent_config_for_eval\(agent_config\)\s+agent_config\.enable_prompt_extensions'

# Process each file
for file_path in run_infer_files:
    print(f"Processing {file_path}...")
    
    # Read the file content
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Fix the indentation
    if 'agent_config = update_agent_config_for_eval(agent_config)' in content:
        # Find the indentation level
        match = re.search(pattern, content, re.DOTALL)
        if match:
            indentation = match.group(1)
            # Fix the indentation
            fixed_content = content.replace(
                f"{indentation}agent_config = config.get_agent_config(metadata.agent_class)\nagent_config = update_agent_config_for_eval(agent_config)",
                f"{indentation}agent_config = config.get_agent_config(metadata.agent_class)\n{indentation}agent_config = update_agent_config_for_eval(agent_config)"
            )
            
            # Write the updated content back to the file
            with open(file_path, 'w') as file:
                file.write(fixed_content)
            
            print(f"  Updated successfully")
        else:
            print(f"  No match found")
    else:
        print(f"  No update needed")

print("Done!")