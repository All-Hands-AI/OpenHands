"""Test vi_mode CLI argument functionality."""

import argparse
import tempfile
from pathlib import Path

import pytest

from openhands.core.config.arg_utils import get_cli_parser
from openhands.core.config.utils import setup_config_from_args


def test_vi_mode_cli_argument():
    """Test that --vi-mode CLI argument sets vi_mode to True."""
    parser = get_cli_parser()
    args = parser.parse_args(['cli', '--vi-mode'])
    
    assert args.vi_mode is True
    
    config = setup_config_from_args(args)
    assert config.cli.vi_mode is True


def test_vi_mode_default():
    """Test that vi_mode defaults to False."""
    parser = get_cli_parser()
    args = parser.parse_args(['cli'])
    
    assert args.vi_mode is False
    
    config = setup_config_from_args(args)
    assert config.cli.vi_mode is False


def test_vi_mode_config_file():
    """Test that vi_mode can be set via config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[cli]\nvi_mode = true\n')
        config_file = f.name
    
    try:
        parser = get_cli_parser()
        args = parser.parse_args(['cli', '--config-file', config_file])
        
        # CLI arg should be False (not set)
        assert args.vi_mode is False
        
        # But config should load vi_mode from file
        config = setup_config_from_args(args)
        assert config.cli.vi_mode is True
    finally:
        Path(config_file).unlink()


def test_vi_mode_cli_overrides_config():
    """Test that CLI argument overrides config file setting."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write('[cli]\nvi_mode = false\n')
        config_file = f.name
    
    try:
        parser = get_cli_parser()
        args = parser.parse_args(['cli', '--config-file', config_file, '--vi-mode'])
        
        # CLI arg should be True
        assert args.vi_mode is True
        
        # Config should use CLI override
        config = setup_config_from_args(args)
        assert config.cli.vi_mode is True
    finally:
        Path(config_file).unlink()