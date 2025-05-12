#!/usr/bin/env python3
import os
import re
import ast
from typing import List, Tuple, Optional

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

def find_files_with_log_in_except(directory: str, exclude_dirs: List[str] = None) -> List[str]:
    """Find all Python files in the directory that have logger statements in except blocks."""
    if exclude_dirs is None:
        exclude_dirs = []
    
    files_with_logs = []
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                logs = find_log_statements_in_except_blocks(file_path)
                if logs:
                    files_with_logs.append(file_path)
                    print(f"{file_path}:")
                    for line_no, log_level, line in logs:
                        print(f"  Line {line_no}: {log_level} - {line.strip()}")
    
    return files_with_logs

if __name__ == "__main__":
    # Find all Python files in the openhands directory that have logger statements in except blocks
    # Exclude the evaluation directory
    find_files_with_log_in_except('/workspace/OpenHands/openhands', ['evaluation'])