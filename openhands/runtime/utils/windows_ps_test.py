import os
import subprocess
import tempfile
from pathlib import Path
import time

def test_powershell_basic():
    """Test basic PowerShell functionality without complex initialization."""
    print("==== PowerShell Basic Test ====")
    
    # Check PowerShell version
    try:
        result = subprocess.run(
            ["powershell", "-Command", "$PSVersionTable.PSVersion"], 
            capture_output=True, 
            text=True,
            check=False
        )
        print(f"PowerShell version check result:")
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
    except Exception as e:
        print(f"Failed to check PowerShell version: {e}")
    
    # Create a simple PowerShell script
    temp_dir = Path(tempfile.mkdtemp())
    test_script = temp_dir / "test.ps1"
    
    print(f"Created temp directory: {temp_dir}")
    
    # Very simple script without any complex logic
    script_content = """
Write-Output "TEST_MARKER_START"
Write-Output "PowerShell is working"
$PSVersionTable.PSVersion
Get-Location
Write-Output "TEST_MARKER_END"
"""
    
    try:
        test_script.write_text(script_content)
        print(f"Wrote test script to: {test_script}")
        
        # Run the script directly
        print("Running script directly...")
        result = subprocess.run(
            ["powershell", "-File", str(test_script)],
            capture_output=True,
            text=True,
            check=False
        )
        print(f"Script execution result:")
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        # Now try running with a pipe to test stdin/stdout communication
        print("\nRunning with pipe to test communication...")
        process = subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send a simple command
        print("Sending command through pipe...")
        process.stdin.write("Write-Output 'Hello through pipe'\n")
        process.stdin.flush()
        time.sleep(0.5)
        
        # Read output
        output = process.stdout.readline()
        print(f"Output from pipe: {output}")
        
        # Send another command
        process.stdin.write("exit\n")
        process.stdin.flush()
        
        # Get final output
        stdout, stderr = process.communicate(timeout=2)
        print(f"Final stdout: {stdout}")
        print(f"Final stderr: {stderr}")
        
    except Exception as e:
        print(f"Error testing PowerShell: {e}")
    finally:
        try:
            # Clean up
            if test_script.exists():
                test_script.unlink()
            os.rmdir(temp_dir)
        except:
            print("Failed to clean up temp files")
    
    print("==== Test Complete ====")

def test_powershell_file_output():
    """Test PowerShell file output redirection."""
    print("\n==== PowerShell File Output Test ====")
    
    temp_dir = Path(tempfile.mkdtemp())
    output_file = temp_dir / "output.txt"
    test_script = temp_dir / "test_output.ps1"
    
    print(f"Created temp directory: {temp_dir}")
    
    # Script that writes to a file
    script_content = f"""
Write-Output "Testing file output" | Out-File -FilePath "{output_file}" -Encoding utf8
Write-Output "File should have been written to: {output_file}"
"""
    
    try:
        test_script.write_text(script_content)
        print(f"Wrote test script to: {test_script}")
        
        # Run the script
        result = subprocess.run(
            ["powershell", "-File", str(test_script)],
            capture_output=True,
            text=True,
            check=False
        )
        print(f"Script execution result:")
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        # Check if the file was created
        if output_file.exists():
            content = output_file.read_text()
            print(f"Output file exists, content: {content}")
        else:
            print(f"Output file was not created at: {output_file}")
        
    except Exception as e:
        print(f"Error testing PowerShell file output: {e}")
    finally:
        try:
            # Clean up
            for file in [test_script, output_file]:
                if file.exists():
                    file.unlink()
            os.rmdir(temp_dir)
        except:
            print("Failed to clean up temp files")
    
    print("==== Test Complete ====")

if __name__ == "__main__":
    test_powershell_basic()
    test_powershell_file_output() 