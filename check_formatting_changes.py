#!/usr/bin/env python3
"""
Script to identify files with only formatting changes.
"""

import subprocess
import re
import sys

def get_changed_files():
    """Get list of files changed from main branch."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "main"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip().split('\n')

def is_formatting_only_change(file_path):
    """Check if a file has only formatting changes."""
    try:
        # Get the diff for the file
        result = subprocess.run(
            ["git", "diff", "main", "--", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        diff = result.stdout
        
        # Skip binary files or new files
        if "Binary files" in diff or "new file mode" in diff:
            return False
            
        # Remove diff headers and line numbers
        lines = diff.split('\n')
        content_lines = [
            line for line in lines 
            if not line.startswith('diff --git') 
            and not line.startswith('index ') 
            and not line.startswith('---') 
            and not line.startswith('+++')
            and not re.match(r'^@@ .* @@', line)
        ]
        
        # Check if all changes are whitespace/formatting only
        for line in content_lines:
            if not line.startswith('+') and not line.startswith('-'):
                continue
                
            # Remove the +/- prefix
            content = line[1:]
            
            # If there's a line with actual code changes (not just whitespace/indentation)
            # then this is not a formatting-only change
            if content.strip() and not line.strip() in ['+', '-']:
                # Check if the corresponding line exists with opposite sign
                opposite_sign = '-' if line.startswith('+') else '+'
                opposite_line = opposite_sign + content
                
                # If we can't find the opposite line, it's a content change
                if opposite_line not in content_lines:
                    return False
        
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    changed_files = get_changed_files()
    formatting_only = []
    
    for file_path in changed_files:
        if is_formatting_only_change(file_path):
            formatting_only.append(file_path)
            
    print("Files with only formatting changes:")
    for file in formatting_only:
        print(f"  {file}")
    
    print(f"\nTotal: {len(formatting_only)} files with only formatting changes")

if __name__ == "__main__":
    main()