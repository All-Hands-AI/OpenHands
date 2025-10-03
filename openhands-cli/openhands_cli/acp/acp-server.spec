# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for OpenHands ACP Server.

This spec file configures PyInstaller to create a standalone executable
for the OpenHands Agent Client Protocol (ACP) Server application.
"""

from pathlib import Path
import os
import sys
from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
    copy_metadata
)

# Get the project root directory (current working directory when running PyInstaller)
project_root = Path.cwd()

a = Analysis(
    ['__main__.py'],
    pathex=[str(project_root / 'openhands' / 'agent_server' / 'acp')],
    binaries=[],
    datas=[
        # Include any data files that might be needed
        # Add more data files here if needed in the future
        *collect_data_files('tiktoken'),
        *collect_data_files('tiktoken_ext'),
        *collect_data_files('litellm'),
        *collect_data_files('fastmcp'),
        *collect_data_files('mcp'),
        # Include Jinja prompt templates required by the agent SDK
        *collect_data_files('openhands.sdk.agent', includes=['prompts/*.j2']),
        *collect_data_files('openhands.sdk.context.condenser', includes=['prompts/*.j2']),
        *collect_data_files('openhands.sdk.context.prompts', includes=['templates/*.j2']),
        # Include package metadata for importlib.metadata
        *copy_metadata('fastmcp'),
        *copy_metadata('agent-client-protocol'),
    ],
    hiddenimports=[
        *collect_submodules('openhands.sdk'),
        *collect_submodules('openhands.tools'),
        *collect_submodules('openhands.agent_server'),
        *collect_submodules('openhands.agent_server.acp'),

        *collect_submodules('tiktoken'),
        *collect_submodules('tiktoken_ext'),
        *collect_submodules('litellm'),
        *collect_submodules('fastmcp'),
        *collect_submodules('acp'),  # Agent Client Protocol SDK
        # Include mcp but exclude Agent Server parts that require typer
        'mcp.types',
        'mcp.client',
        'mcp.server',
        'mcp.shared',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce binary size
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'IPython',
        'jupyter',
        'notebook',
        # Exclude mcp CLI parts that cause issues
        'mcp.cli',
        'mcp.cli.cli',
        # Exclude the main agent server to reduce size (ACP server is standalone)
        'openhands.agent_server.api',
        'openhands.agent_server.app',
    ],
    noarchive=False,
    # IMPORTANT: do not use optimize=2 (-OO) because it strips docstrings used by PLY/bashlex grammar
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='openhands-acp-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip debug symbols to reduce size
    upx=True,    # Use UPX compression if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)