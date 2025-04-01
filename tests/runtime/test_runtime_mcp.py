"""Runtime tests for the MCP wrapper functionality."""

from conftest import _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction, IPythonRunCellAction


def test_mcp_postgres_integration(temp_dir, runtime_cls):
    """Test MCP wrapper integration with a postgres server."""
    runtime, _ = _load_runtime(
        temp_dir,
        runtime_cls,
        use_host_network=True,
    )

    # Install postgres
    action = CmdRunAction(
        command='sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    # Start PostgreSQL service using `service` command
    action = CmdRunAction(command='sudo service postgresql start')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    # Set password for `postgres` user
    action = CmdRunAction(
        command='sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD \'yourpassword\';"'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    # Create test table and data
    action = CmdRunAction(
        command="""
        sudo -u postgres psql -c "CREATE TABLE students (id SERIAL PRIMARY KEY, name TEXT, grade INTEGER);" &&
        sudo -u postgres psql -c "INSERT INTO students (name, grade) VALUES ('Alice', 95), ('Bob', 87), ('Charlie', 92);"
        """
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    # Test MCP wrapper via IPython
    test_code = """
config = {
    "command": "npx",
    "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:yourpassword@localhost:5432/postgres"
    ]
}

# List available tools
tools = await list_tools(config)
print("Available tools:", tools)
assert len(tools) > 0

# Query students table
result = await call_tool(config, "query", {"sql": "SELECT * FROM students;"})
print("Query result:", result)
assert len(result["rows"]) == 3  # We inserted 3 students
"""

    action = IPythonRunCellAction(code=test_code)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Available tools' in obs.content
    assert 'Query result' in obs.content

    _close_test_runtime(runtime)
