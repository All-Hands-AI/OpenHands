# openhands/cli/mcp_preflight.py
from __future__ import annotations

import json
import os
import shlex
import shutil
import sys
from pathlib import Path
from typing import Iterable


def _first_token(cmd: str | list[str]) -> str:
    """Return the binary name from a shell command string or argv list."""
    if isinstance(cmd, list):
        return cmd[0] if cmd else ""
    s = cmd.strip()
    if not s:
        return ""
    try:
        parts = shlex.split(s, posix=(os.name != "nt"))
        return parts[0] if parts else ""
    except Exception:
        # Fallback if quoting is odd; best-effort split on whitespace
        return s.split()[0]


def _extract_commands_from_mcp_config(path: Path) -> list[str | list[str]]:
    """Collect command values from common MCP config shapes."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    cmds: list[str | list[str]] = []

    # Common: {"tools":[{"name":"...","command":"uvx mcp-server-foo --stdio"}]}
    for t in (data.get("tools") or []):
        cmd = t.get("command")
        if (isinstance(cmd, str) and cmd.strip()) or (isinstance(cmd, list) and cmd):
            cmds.append(cmd)

    # Be permissive with alternative key names
    for t in (data.get("servers") or []):
        cmd = t.get("command")
        if (isinstance(cmd, str) and cmd.strip()) or (isinstance(cmd, list) and cmd):
            cmds.append(cmd)

    return cmds


def _missing_binaries(cmds: Iterable[str | list[str]]) -> list[str]:
    seen: set[str] = set()
    missing: list[str] = []
    for cmd in cmds:
        binary = _first_token(cmd)
        if binary and shutil.which(binary) is None and binary not in seen:
            seen.add(binary)
            missing.append(binary)
    return missing


def check_mcp_commands_exist(mcp_config_path: str, *, exit_on_missing: bool = True) -> list[str]:
    """
    Validate that binaries referenced in an MCP config exist on PATH.

    Args:
        mcp_config_path: Path to MCP JSON config file.
        exit_on_missing: If True, print guidance to stderr and sys.exit(1) when one or more are missing.

    Returns:
        The list of missing binaries (possibly empty).
    """
    if not mcp_config_path:
        return []

    path = Path(os.path.expandvars(os.path.expanduser(mcp_config_path)))
    if not path.is_file():
        return []

    try:
        cmds = _extract_commands_from_mcp_config(path)
    except json.JSONDecodeError as e:
        msg = f"Invalid MCP config JSON at {path}:\n{e}"
        if exit_on_missing:
            print(msg, file=sys.stderr)
            raise SystemExit(1)
        return []

    missing = _missing_binaries(cmds)

    if missing and exit_on_missing:
        bullets = "\n  - " + "\n  - ".join(missing)
        plural = "s" if len(missing) > 1 else ""
        print(
            f"Required command{plural} not found on PATH:{bullets}\n\n"
            "Hint: If you launch MCP servers via `uvx`, install Astral uv and ensure `uvx` is on PATH.\n"
            "Windows (PowerShell): irm https://astral.sh/uv/install.ps1 | iex\n"
            "macOS/Linux (bash):  curl -LsSf https://astral.sh/uv/install.sh | sh",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return missing
