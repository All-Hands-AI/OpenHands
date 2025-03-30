import os
import time
from openhands.runtime.utils.direct_windows_bash import DirectWindowsBashSession
from openhands.events.action import CmdRunAction

def main():
    print("=== Testing DirectWindowsBashSession ===")
    
    # Get current directory
    work_dir = os.getcwd()
    print(f"Current directory: {work_dir}")
    
    # Initialize session
    print("Creating PowerShell session...")
    session = DirectWindowsBashSession(work_dir)
    
    try:
        print("Initializing session...")
        session.initialize()
        print("Session initialized!")
        
        # Execute simple command
        print("\nExecuting simple command: Write-Output 'Hello World'")
        result = session.execute(CmdRunAction(command="Write-Output 'Hello World'", is_input=False))
        print(f"Command result type: {type(result).__name__}")
        if hasattr(result, "content"):
            print(f"Content: {result.content!r}")
        else:
            print(f"Error: {result}")
            
        # Execute command with output
        print("\nExecuting command with output: Get-Process | Select-Object -First 3")
        result = session.execute(CmdRunAction(command="Get-Process | Select-Object -First 3", is_input=False))
        if hasattr(result, "content"):
            print(f"Content:\n{result.content}")
        else:
            print(f"Error: {result}")
            
        # Change directory
        print("\nChanging directory: Set-Location '..'")
        result = session.execute(CmdRunAction(command="Set-Location '..'", is_input=False))
        if hasattr(result, "content"):
            print(f"Content: {result.content}")
            print(f"New working directory: {session._cwd}")
        else:
            print(f"Error: {result}")
            
        # Execute command with error
        print("\nExecuting command that should fail: Get-NonExistentCmdlet")
        result = session.execute(CmdRunAction(command="Get-NonExistentCmdlet", is_input=False))
        if hasattr(result, "content"):
            print(f"Content: {result.content}")
            if hasattr(result, "metadata"):
                print(f"Exit code: {result.metadata.exit_code}")
        else:
            print(f"Error: {result}")
    
    finally:
        # Clean up
        print("\nClosing session...")
        session.close()
        print("Session closed")
        
if __name__ == "__main__":
    main() 