# tests/unit/test_mcp_preflight.py
import json
from pathlib import Path

from openhands.cli.mcp_preflight import check_mcp_commands_exist


def test_missing_uvx_detected(tmp_path, monkeypatch):
    # Remove PATH so uvx won't be found
    monkeypatch.setenv("PATH", "")

    cfg = {"tools": [{"name": "fetch", "command": "uvx mcp-server-fetch --stdio"}]}
    cfg_path = Path(tmp_path) / "mcp.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    missing = check_mcp_commands_exist(str(cfg_path), exit_on_missing=False)
    assert "uvx" in missing
