"""
End-to-end tests for OpenHands CLI with ACP mode.

These tests spawn the actual CLI process with --acp flag and verify
basic integration and JSON-RPC communication over stdio.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture
async def cli_process():
    """Fixture that starts the CLI in ACP mode as a subprocess."""
    # Create a temporary directory for conversations
    with tempfile.TemporaryDirectory() as temp_dir:
        env = os.environ.copy()
        env["HOME"] = temp_dir  # CLI uses ~/.openhands/conversations
        env["DEBUG"] = "false"  # Reduce logging noise

        # Get the path to the CLI entry point
        cli_module = "openhands_cli.simple_main"

        # Start the CLI process with --acp flag
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            cli_module,
            "--acp",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        yield process

        # Cleanup
        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except TimeoutError:
            process.kill()
            await process.wait()


async def send_json_rpc(process, method: str, params: dict | None = None, timeout: float = 5.0) -> dict:
    """Send a JSON-RPC request and wait for response."""
    request_id = hash((method, json.dumps(params, sort_keys=True))) % 1000000
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params or {},
    }

    request_str = json.dumps(request) + "\n"
    logger.debug(f"Sending request: {request_str.strip()}")
    process.stdin.write(request_str.encode())
    await process.stdin.drain()

    # Read response - may need to skip notifications and find the matching response
    max_attempts = 50  # Increased to handle non-JSON output lines
    for attempt in range(max_attempts):
        response_line = await asyncio.wait_for(process.stdout.readline(), timeout=timeout)
        logger.debug(f"Received line {attempt+1}: {response_line.decode().strip()}")

        if not response_line:
            raise RuntimeError(f"No response received from CLI process after {attempt+1} attempts")

        try:
            response = json.loads(response_line.decode())
            # Check if this is our response (matching ID) or a notification
            if "id" in response and response["id"] == request_id:
                return response
            # If it's a notification, continue reading
            logger.debug(f"Skipping notification or non-matching response: {response}")
        except json.JSONDecodeError:
            # Skip non-JSON lines (may be debug output that wasn't redirected to stderr)
            logger.warning(f"Skipping non-JSON line: {response_line.decode().strip()}")
            continue

    raise RuntimeError(f"Did not find matching response after {max_attempts} attempts")


async def send_json_rpc_notification(process, method: str, params: dict | None = None):
    """Send a JSON-RPC notification (no response expected)."""
    notification = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
    }

    notification_str = json.dumps(notification) + "\n"
    process.stdin.write(notification_str.encode())
    await process.stdin.drain()


@pytest.mark.asyncio
async def test_e2e_cli_starts_successfully(cli_process):
    """Test that CLI starts successfully with --acp flag."""
    process = cli_process

    # Give it a moment to start
    await asyncio.sleep(0.5)

    # Process should be running
    assert process.returncode is None, "CLI process should still be running"


@pytest.mark.asyncio
async def test_e2e_initialize(cli_process):
    """Test end-to-end initialization of CLI in ACP mode via JSON-RPC."""
    process = cli_process

    # Check stderr for any startup messages
    stderr_task = asyncio.create_task(process.stderr.read(1024))
    try:
        stderr_data = await asyncio.wait_for(stderr_task, timeout=0.5)
        if stderr_data:
            logger.info(f"CLI stderr at start: {stderr_data.decode()}")
    except TimeoutError:
        stderr_task.cancel()

    # Send initialize request
    try:
        response = await send_json_rpc(
            process,
            "initialize",
            {"protocolVersion": "1.0", "apiKey": "test_key_123"}
        )
    except Exception:
        # Try to get stderr for debugging
        try:
            stderr_data = await asyncio.wait_for(process.stderr.read(4096), timeout=0.5)
            logger.error(f"CLI stderr after error: {stderr_data.decode()}")
        except Exception:  # noqa: S110
            pass
        raise

    # Check response structure
    assert "result" in response, f"Expected result in response, got: {response}"
    result = response["result"]
    # Protocol version can be returned as int (1) or float (1.0) or string ("1.0")
    assert result["protocolVersion"] in [1, 1.0, "1.0"]
    # Check for agent capabilities (might be named "agentCapabilities" in newer protocol)
    assert "agentCapabilities" in result or "capabilities" in result
    if "agentCapabilities" in result:
        assert "promptCapabilities" in result["agentCapabilities"]
    else:
        assert "prompting" in result["capabilities"]


@pytest.mark.asyncio
async def test_e2e_authenticate_with_llm_config(cli_process):
    """Test authentication with LLM configuration via JSON-RPC."""
    process = cli_process

    # Initialize first
    await send_json_rpc(
        process,
        "initialize",
        {"protocolVersion": "1.0", "apiKey": "test_key_123"}
    )

    # Authenticate with LLM config
    auth_response = await send_json_rpc(
        process,
        "authenticate",
        {
            "methodId": "llm-config",
            "authMethod": {
                "method": "llm-config",
                "config": {
                    "model": "gpt-4",
                    "api_key": "sk-test123",
                    "base_url": "https://api.openai.com/v1",
                },
            }
        }
    )

    assert "result" in auth_response, f"Expected result, got: {auth_response}"
    # Authentication response is just an acknowledgment
    result = auth_response["result"]
    # May have a success field or just be empty/acknowledgment
    assert result is not None


@pytest.mark.asyncio
@pytest.mark.skip(
    reason=(
        "session/new produces formatted output to stdout which interferes "
        "with JSON-RPC - needs fix in OpenHands CLI"
    )
)
async def test_e2e_new_session(cli_process):
    """Test creating a new session through CLI via JSON-RPC.

    Note: This test is currently skipped because the OpenHands CLI prints
    formatted output (like "System Prompt" boxes) to stdout during session
    creation, which interferes with JSON-RPC communication. This should be
    fixed by redirecting all such output to stderr.
    """
    process = cli_process

    # Initialize
    await send_json_rpc(
        process,
        "initialize",
        {"protocolVersion": "1.0", "apiKey": "test_key_123"}
    )

    # Authenticate
    await send_json_rpc(
        process,
        "authenticate",
        {
            "methodId": "llm-config",
            "authMethod": {
                "method": "llm-config",
                "config": {
                    "model": "gpt-4",
                    "api_key": "sk-test123",
                },
            }
        }
    )

    # Create new session with required parameters
    session_response = await send_json_rpc(
        process,
        "session/new",
        {
            "cwd": "/tmp",
            "mcpServers": []
        },
        timeout=30.0  # Longer timeout for session creation
    )

    assert "result" in session_response
    result = session_response["result"]
    assert "sessionId" in result
    assert len(result["sessionId"]) > 0


@pytest.mark.asyncio
async def test_e2e_initialize_without_api_key(cli_process):
    """Test initialization without providing an API key."""
    process = cli_process

    # Send initialize request without API key
    response = await send_json_rpc(
        process,
        "initialize",
        {"protocolVersion": "1.0"}
    )

    assert "result" in response
    result = response["result"]
    # Protocol version can be returned as int (1) or float (1.0) or string ("1.0")
    assert result["protocolVersion"] in [1, 1.0, "1.0"]
    # Should still work but will require authentication later


@pytest.mark.asyncio
async def test_e2e_cli_handles_invalid_json(cli_process):
    """Test that CLI handles invalid JSON gracefully."""
    process = cli_process

    # Send invalid JSON
    process.stdin.write(b"invalid json\n")
    await process.stdin.drain()

    # Give it time to process
    await asyncio.sleep(0.5)

    # Process should still be running
    assert process.returncode is None


@pytest.mark.asyncio
async def test_e2e_multiple_requests(cli_process):
    """Test that CLI can handle multiple sequential requests."""
    process = cli_process

    # Send multiple initialize requests
    for i in range(3):
        response = await send_json_rpc(
            process,
            "initialize",
            {"protocolVersion": "1.0", "apiKey": f"test_key_{i}"}
        )
        assert "result" in response


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
