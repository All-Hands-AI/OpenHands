"""Tests for the setup script."""

import os
import time
from pathlib import Path

import pytest
from conftest import (
    _close_test_runtime,
    _load_runtime,
)

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction, FileWriteAction, FileReadAction
from openhands.events.observation import CmdOutputObservation, ErrorObservation, FileWriteObservation, FileReadObservation
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.core.setup import initialize_repository_for_runtime


def test_initialize_repository_for_runtime(temp_dir, runtime_cls, run_as_openhands):
    """Test that the initialize_repository_for_runtime function works."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    repository_dir = initialize_repository_for_runtime(runtime, "https://github.com/All-Hands-AI/OpenHands")
    assert repository_dir is not None
    assert repository_dir == "OpenHands"


def test_maybe_run_setup_script(temp_dir, runtime_cls, run_as_openhands):
    """Test that setup script is executed when it exists."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    
    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(FileWriteAction(path=setup_script, content="#!/bin/bash\necho 'Hello World' >> README.md\n"))
    assert isinstance(write_obs, FileWriteObservation)
    
    # Run setup script
    runtime.maybe_run_setup_script()
    
    # Verify script was executed by checking output
    read_obs = runtime.read(FileReadAction(path='README.md'))
    assert isinstance(read_obs, FileReadObservation)
    assert read_obs.content == "Hello World\n"


def test_maybe_run_setup_script_with_long_timeout(temp_dir, runtime_cls, run_as_openhands):
    """Test that setup script is executed when it exists."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    
    setup_script = '.openhands/setup.sh'
    write_obs = runtime.write(FileWriteAction(path=setup_script, content="#!/bin/bash\nsleep 15 && echo 'Hello World' >> README.md\n"))
    assert isinstance(write_obs, FileWriteObservation)
    
    # Run setup script
    runtime.maybe_run_setup_script()
    
    # Verify script was executed by checking output
    read_obs = runtime.read(FileReadAction(path='README.md'))
    assert isinstance(read_obs, FileReadObservation)
    assert read_obs.content == "Hello World\n"

