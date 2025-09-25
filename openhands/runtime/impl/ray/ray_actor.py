"""Ray execution actor for distributed OpenHands execution."""

import asyncio
import os
import subprocess
import tempfile
import traceback
from typing import Any, Dict
import logging

import ray

logger = logging.getLogger(__name__)


@ray.remote
class RayExecutionActor:
    """Ray actor for executing commands in an isolated environment."""
    
    def __init__(self, workspace_path: str, env_vars: dict[str, str]):
        """Initialize the Ray execution actor.
        
        Args:
            workspace_path: Path to the workspace directory
            env_vars: Environment variables to set
        """
        self.workspace_path = workspace_path
        self.env_vars = env_vars
        self.current_dir = workspace_path
        
        # Ensure workspace directory exists
        os.makedirs(workspace_path, exist_ok=True)
        
        # Change to workspace directory
        os.chdir(workspace_path)
        
        # IPython kernel management
        self.ipython_kernel = None
        
        logger.info(f"RayExecutionActor initialized with workspace: {workspace_path}")
    
    async def execute_action(self, action_data: dict) -> dict[str, Any]:
        """Execute an action based on its type."""
        action_type = action_data.get('type')
        
        # Route to appropriate handler
        if action_type == 'CmdRunAction':
            return await self.execute_command(
                action_data['command'], 
                action_data.get('timeout', 60)
            )
        elif action_type == 'FileReadAction':
            return await self.read_file(action_data['path'])
        elif action_type == 'FileWriteAction':
            return await self.write_file(action_data['path'], action_data['content'])
        elif action_type == 'FileEditAction':
            return await self.edit_file(
                action_data['path'],
                action_data['new_str'],
                action_data.get('old_str'),
                action_data.get('start_line'),
                action_data.get('end_line')
            )
        elif action_type == 'IPythonRunCellAction':
            return await self.run_ipython(
                action_data['code'],
                action_data.get('kernel_init_code')
            )
        elif action_type == 'BrowseURLAction':
            return await self.browse_url(action_data['url'])
        elif action_type == 'BrowseInteractiveAction':
            return await self.browse_interactive(action_data.get('browser_actions', []))
        else:
            return {
                'success': False,
                'error': f'Unsupported action type: {action_type}'
            }
    
    async def execute_command(self, command: str, timeout: int = 60) -> dict[str, Any]:
        """Execute a shell command in the workspace."""
        try:
            logger.info(f"Executing command: {command}")
            
            # Prepare environment
            env = os.environ.copy()
            env.update(self.env_vars)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                return {
                    'exit_code': process.returncode,
                    'stdout': stdout.decode('utf-8', errors='replace'),
                    'stderr': stderr.decode('utf-8', errors='replace'),
                }
                
            except asyncio.TimeoutError:
                process.kill()
                return {
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': f'Command timed out after {timeout} seconds',
                }
                
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                'exit_code': 1,
                'stdout': '',
                'stderr': str(e),
            }
    
    async def read_file(self, file_path: str) -> dict[str, Any]:
        """Read a file from the filesystem."""
        try:
            # Convert to absolute path relative to workspace
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.workspace_path, file_path)
            
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            return {
                'success': True,
                'content': content,
            }
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def write_file(self, file_path: str, content: str) -> dict[str, Any]:
        """Write content to a file."""
        try:
            # Convert to absolute path relative to workspace
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.workspace_path, file_path)
            
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return {
                'success': True,
                'content': content,
            }
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def edit_file(
        self, 
        file_path: str, 
        new_str: str, 
        old_str: str = None,
        start_line: int = None, 
        end_line: int = None
    ) -> dict[str, Any]:
        """Edit a file with string replacement or line-based editing."""
        try:
            # Convert to absolute path relative to workspace
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.workspace_path, file_path)
            
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
            
            # Read current content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            if old_str is not None:
                # String replacement mode
                original_content = ''.join(lines)
                if old_str not in original_content:
                    return {
                        'success': False,
                        'error': f'String to replace not found: {old_str[:50]}...'
                    }
                
                new_content = original_content.replace(old_str, new_str)
                
            elif start_line is not None and end_line is not None:
                # Line range replacement mode (1-indexed)
                start_idx = max(0, start_line - 1)
                end_idx = min(len(lines), end_line)
                
                # Replace lines
                new_lines = lines[:start_idx] + [new_str + '\n'] + lines[end_idx:]
                new_content = ''.join(new_lines)
                
            else:
                return {
                    'success': False,
                    'error': 'Must specify either old_str or start_line/end_line'
                }
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return {
                'success': True,
                'content': new_content,
            }
            
        except Exception as e:
            logger.error(f"Error editing file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def run_ipython(self, code: str, kernel_init_code: str = None) -> dict[str, Any]:
        """Run IPython code (placeholder implementation)."""
        try:
            # For now, just echo the code as this is a basic implementation
            # In a full implementation, this would use IPython kernel
            
            logger.info(f"Running IPython code: {code[:100]}...")
            
            # Simple code execution for demonstration
            if kernel_init_code:
                full_code = kernel_init_code + '\n' + code
            else:
                full_code = code
            
            # Use exec for simple Python code execution
            # Note: This is a simplified implementation
            local_vars = {}
            global_vars = {'__builtins__': __builtins__}
            
            try:
                exec(full_code, global_vars, local_vars)
                
                # Capture any print output (simplified)
                result_content = f"Code executed successfully:\n{code}"
                
            except Exception as exec_error:
                result_content = f"Execution error: {str(exec_error)}"
            
            return {
                'success': True,
                'content': result_content,
            }
            
        except Exception as e:
            logger.error(f"Error running IPython code: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def browse_url(self, url: str) -> dict[str, Any]:
        """Browse a URL (placeholder implementation)."""
        try:
            logger.info(f"Browsing URL: {url}")
            
            # Placeholder implementation - would integrate with browser automation
            result_content = f"Browsed URL: {url}\n"
            result_content += "Note: This is a placeholder implementation.\n"
            result_content += "Full browser integration would be implemented here."
            
            return {
                'success': True,
                'content': result_content,
                'url': url,
            }
            
        except Exception as e:
            logger.error(f"Error browsing URL: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def browse_interactive(self, browser_actions: list) -> dict[str, Any]:
        """Perform interactive browsing actions (placeholder implementation)."""
        try:
            logger.info(f"Interactive browsing with {len(browser_actions)} actions")
            
            result_content = "Interactive browsing not fully implemented in Ray actor yet.\n"
            result_content += f"Requested actions: {browser_actions}"
            
            return {
                'success': True,
                'content': result_content,
                'url': 'about:blank',
            }
            
        except Exception as e:
            logger.error(f"Error with interactive browsing: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def ping(self) -> dict[str, Any]:
        """Health check method for worker pool monitoring."""
        import time
        return {
            'success': True,
            'timestamp': time.time(),
            'workspace_path': self.workspace_path,
        }