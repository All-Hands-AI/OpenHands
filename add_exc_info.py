#!/usr/bin/env python3
import os
import re
import ast
from typing import List, Tuple, Dict, Set

def find_log_statements_in_except_blocks(file_path: str) -> List[Tuple[int, str, str]]:
    """
    Find logger statements in except blocks that don't have exc_info=True.
    
    Returns a list of tuples (line_number, log_level, log_statement)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        print(f"Syntax error in {file_path}")
        return []
    
    results = []
    
    class LogVisitor(ast.NodeVisitor):
        def __init__(self):
            self.in_except_block = False
            self.except_line_no = 0
        
        def visit_ExceptHandler(self, node):
            old_in_except = self.in_except_block
            self.in_except_block = True
            self.except_line_no = node.lineno
            self.generic_visit(node)
            self.in_except_block = old_in_except
        
        def visit_Call(self, node):
            if not self.in_except_block:
                self.generic_visit(node)
                return
            
            # Check if it's a logger call
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id in ['logger', 'openhands_logger']:
                    log_level = node.func.attr
                    if log_level in ['error', 'warning', 'critical']:
                        # Check if exc_info is already set
                        has_exc_info = False
                        for keyword in node.keywords:
                            if keyword.arg == 'exc_info':
                                has_exc_info = True
                                break
                        
                        if not has_exc_info:
                            # Get the line from the source code
                            line_no = node.lineno
                            line = content.splitlines()[line_no - 1]
                            results.append((line_no, log_level, line))
            
            self.generic_visit(node)
    
    visitor = LogVisitor()
    visitor.visit(tree)
    return results

def add_exc_info_to_log_statements(file_path: str) -> bool:
    """
    Add exc_info=True to logger statements in except blocks.
    
    Returns True if the file was modified, False otherwise.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    log_statements = find_log_statements_in_except_blocks(file_path)
    if not log_statements:
        return False
    
    # Parse the file with AST to get accurate positions
    try:
        tree = ast.parse(content)
    except SyntaxError:
        print(f"Syntax error in {file_path}, skipping")
        return False
    
    # Use regular expressions to add exc_info=True
    modified_content = content
    
    # Define patterns for different logger call styles
    patterns = [
        # Pattern for logger.error('message')
        r'(logger\.(error|warning|critical)\([^)]*)\)',
        # Pattern for logger.error(f'message', param=value)
        r'(logger\.(error|warning|critical)\([^,]*,[^)]*)\)',
        # Pattern for multiline logger calls
        r'(logger\.(error|warning|critical)\([^)]*\n[^)]*)\)',
        # Pattern for openhands_logger
        r'(openhands_logger\.(error|warning|critical)\([^)]*)\)'
    ]
    
    # Apply each pattern
    for pattern in patterns:
        # Find all matches
        matches = list(re.finditer(pattern, modified_content))
        
        # Process matches in reverse order to avoid position shifts
        for match in reversed(matches):
            # Check if exc_info is already present
            if 'exc_info=' not in match.group(0):
                # Get the matched text
                matched_text = match.group(0)
                
                # Check if there are already parameters (indicated by a comma)
                if ',' in matched_text:
                    # Add exc_info=True as an additional parameter
                    replacement = f"{match.group(1)}, exc_info=True)"
                else:
                    # Add exc_info=True as the first parameter
                    replacement = f"{match.group(1)}, exc_info=True)"
                
                # Replace in the content
                modified_content = modified_content[:match.start()] + replacement + modified_content[match.end():]
    
    # Check if content was modified
    if modified_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"Modified {file_path}")
        return True
    
    return False

def process_directory(directory: str, exclude_dirs: List[str] = None) -> List[str]:
    """
    Process all Python files in the directory and add exc_info=True to logger statements in except blocks.
    
    Returns a list of modified files.
    """
    if exclude_dirs is None:
        exclude_dirs = []
    
    modified_files = []
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if add_exc_info_to_log_statements(file_path):
                    modified_files.append(file_path)
    
    return modified_files

if __name__ == "__main__":
    # Process all Python files in the openhands directory
    # Exclude the evaluation directory
    modified_files = process_directory('/workspace/OpenHands/openhands', ['evaluation'])
    print(f"Modified {len(modified_files)} files")