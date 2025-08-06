import os
import subprocess
import sys
import tempfile


def test_fastmcp_import_and_version():
    """Test that fastmcp can be imported and verify its version.

    This test confirms the upgrade was successful.
    """
    # Create a temporary Python script to check fastmcp version
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
        f.write("""
import fastmcp
import sys
print(f"FastMCP version: {fastmcp.__version__}")
sys.exit(0)
        """)
        script_path = f.name

    try:
        # Run the script using the current Python interpreter
        result = subprocess.run(
            [sys.executable, script_path], capture_output=True, text=True, check=True
        )

        # Check the output
        print(result.stdout)
        assert 'FastMCP version: 2.11.1' in result.stdout, (
            f'Expected fastmcp version 2.11.1, got: {result.stdout}'
        )

    finally:
        # Clean up
        if os.path.exists(script_path):
            os.unlink(script_path)


def test_fastmcp_imports():
    """Test that we can import key components from fastmcp."""
    # Create a temporary Python script to test imports
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
        f.write("""
import sys
import fastmcp

try:
    # Test importing key components
    from fastmcp import Client
    from fastmcp import Context
    from fastmcp import FastMCP

    # Test importing from server module
    from fastmcp.server import server

    # Print success message with imported modules
    print("Successfully imported key fastmcp components:")
    print(f"- fastmcp version: {fastmcp.__version__}")
    print(f"- Client: {Client}")
    print(f"- Context: {Context}")
    print(f"- FastMCP: {FastMCP}")
    print(f"- server module: {server}")

    sys.exit(0)
except Exception as e:
    print(f"Error importing fastmcp components: {e}")
    sys.exit(1)
        """)
        script_path = f.name

    try:
        # Run the script using the current Python interpreter
        result = subprocess.run(
            [sys.executable, script_path], capture_output=True, text=True
        )

        # Check the output
        print(result.stdout)
        assert result.returncode == 0, (
            f'Failed to import fastmcp components: {result.stderr}'
        )
        assert 'Successfully imported key fastmcp components' in result.stdout
        assert 'fastmcp version: 2.11.1' in result.stdout

    finally:
        # Clean up
        if os.path.exists(script_path):
            os.unlink(script_path)


def test_fastmcp_client_creation():
    """Test that we can create a fastmcp client with the upgraded version."""
    # Create a temporary Python script to test client creation
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
        f.write("""
import sys
import asyncio
import fastmcp
from fastmcp import Client

async def test_client():
    try:
        # Import the transport to create a client
        from fastmcp.client.transports import SSETransport

        # Create a transport
        transport = SSETransport(url="http://example.com")

        # Create a client instance using the new Client.new() factory method
        client = Client.new(transport)

        # Just verify we can create the client
        print("Successfully created fastmcp Client instance")
        print(f"- Client type: {type(client)}")
        print(f"- Client repr: {repr(client)}")
        return True
    except Exception as e:
        print(f"Error creating fastmcp Client: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_client())
    sys.exit(0 if success else 1)
        """)
        script_path = f.name

    try:
        # Run the script using the current Python interpreter
        result = subprocess.run(
            [sys.executable, script_path], capture_output=True, text=True
        )

        # Check the output
        print(result.stdout)
        assert result.returncode == 0, (
            f'Failed to create fastmcp Client: {result.stderr}'
        )
        assert 'Successfully created fastmcp Client instance' in result.stdout

    finally:
        # Clean up
        if os.path.exists(script_path):
            os.unlink(script_path)
