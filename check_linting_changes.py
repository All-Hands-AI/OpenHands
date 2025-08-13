#!/usr/bin/env python3
"""
Script to identify files that only have linting/whitespace changes
and can be safely reverted to main branch version.
"""

import subprocess
import sys
import re

def get_diff_stats(file_path):
    """Get diff statistics for a file."""
    try:
        result = subprocess.run(
            ['git', 'diff', 'origin/main', '--', file_path],
            capture_output=True,
            text=True,
            check=True
        )
        diff_content = result.stdout
        
        if not diff_content.strip():
            return None, 0, 0, 0
            
        # Count lines
        added_lines = len([line for line in diff_content.split('\n') if line.startswith('+')])
        removed_lines = len([line for line in diff_content.split('\n') if line.startswith('-')])
        
        # Check if changes are only whitespace/formatting
        meaningful_changes = 0
        for line in diff_content.split('\n'):
            if line.startswith('+') or line.startswith('-'):
                # Skip diff headers
                if line.startswith('+++') or line.startswith('---'):
                    continue
                    
                # Remove the +/- prefix
                content = line[1:]
                
                # Check if this is a meaningful change (not just whitespace/imports)
                if content.strip() and not is_linting_change(content):
                    meaningful_changes += 1
        
        return diff_content, added_lines, removed_lines, meaningful_changes
        
    except subprocess.CalledProcessError:
        return None, 0, 0, 0

def is_linting_change(line):
    """Check if a line represents a linting change."""
    line = line.strip()
    
    # Empty lines
    if not line:
        return True
        
    # Import reordering/removal
    if line.startswith('import ') or line.startswith('from '):
        return True
        
    # Docstring formatting changes
    if line.startswith('"""') or line.startswith("'''"):
        return True
        
    # Comment changes
    if line.startswith('#'):
        return True
        
    # Common linting patterns
    linting_patterns = [
        r'^\s*$',  # Empty lines
        r'^\s*#',  # Comments
        r'^\s*(import|from)\s+',  # Imports
        r'^\s*"""',  # Docstrings
        r'^\s*\'\'\'',  # Docstrings
    ]
    
    for pattern in linting_patterns:
        if re.match(pattern, line):
            return True
            
    return False

def main():
    # Get list of changed files
    result = subprocess.run(
        ['git', 'diff', 'origin/main', '--name-only'],
        capture_output=True,
        text=True,
        check=True
    )
    
    changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
    
    # Core LLM risk analyzer files that should NOT be reverted
    core_files = {
        'openhands/security/',
        'openhands/agenthub/codeact_agent/tools/security_utils',
        'openhands/core/config/security_config.py',
        'frontend/src/components/features/settings/settings-switch-with-tooltip.tsx',
        'frontend/src/routes/app-settings.tsx',
        'frontend/src/i18n/',
        'tests/unit/test_security.py',
        'config.template.toml',
        'openhands/storage/data_models/settings.py',
        'openhands/cli/main.py',
        'openhands/cli/tui.py',
    }
    
    linting_only_files = []
    
    for file_path in changed_files:
        # Skip core feature files
        if any(core_path in file_path for core_path in core_files):
            print(f"KEEP (core): {file_path}")
            continue
            
        # Skip non-Python files for now (except specific ones we know about)
        if not (file_path.endswith('.py') or file_path.endswith('.j2') or file_path.endswith('.toml')):
            continue
            
        diff_content, added, removed, meaningful = get_diff_stats(file_path)
        
        if diff_content is None:
            continue
            
        # If no meaningful changes, it's likely just linting
        if meaningful <= 2:  # Allow for very minor changes
            print(f"REVERT (linting): {file_path} (meaningful changes: {meaningful})")
            linting_only_files.append(file_path)
        else:
            print(f"KEEP (meaningful): {file_path} (meaningful changes: {meaningful})")
    
    print(f"\nFound {len(linting_only_files)} files with only linting changes")
    
    if linting_only_files:
        print("\nFiles to revert:")
        for f in linting_only_files:
            print(f"  {f}")
            
        return linting_only_files
    
    return []

if __name__ == '__main__':
    files_to_revert = main()
    
    # Write to file for use by shell script
    with open('/tmp/files_to_revert.txt', 'w') as f:
        for file_path in files_to_revert:
            f.write(f"{file_path}\n")