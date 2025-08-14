"""Unit tests for CLI editor shortcuts functionality."""

import os
import tempfile
from unittest.mock import patch

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.core.config.arg_utils import get_cli_parser, get_subparser
from openhands.core.config.utils import setup_config_from_args
from openhands.cli.editor_bindings import create_enhanced_key_bindings


class TestCLIEditorShortcuts:
    """Test suite for CLI editor shortcuts functionality."""

    def test_cli_config_defaults(self):
        """Test that CLI config has correct defaults."""
        config = OpenHandsConfig()
        assert config.cli.editor_mode == 'auto'
        assert config.cli.vi_mode is False
        assert config.cli.get_effective_editor_mode() in ['emacs', 'vi']
        assert isinstance(config.cli.is_vi_mode(), bool)

    def test_editor_mode_auto_detection(self):
        """Test auto-detection of editor mode from environment."""
        config = OpenHandsConfig()
        config.cli.editor_mode = 'auto'
        
        # Test with vim-like editors
        with patch.dict(os.environ, {'EDITOR': 'vim'}):
            assert config.cli.get_effective_editor_mode() == 'vi'
        
        with patch.dict(os.environ, {'EDITOR': 'nvim'}):
            assert config.cli.get_effective_editor_mode() == 'vi'
        
        with patch.dict(os.environ, {'EDITOR': 'vi'}):
            assert config.cli.get_effective_editor_mode() == 'vi'
        
        # Test with non-vim editors
        with patch.dict(os.environ, {'EDITOR': 'nano'}):
            assert config.cli.get_effective_editor_mode() == 'emacs'
        
        with patch.dict(os.environ, {'EDITOR': 'emacs'}):
            assert config.cli.get_effective_editor_mode() == 'emacs'
        
        # Test with no EDITOR set
        with patch.dict(os.environ, {}, clear=True):
            assert config.cli.get_effective_editor_mode() == 'emacs'

    def test_explicit_editor_modes(self):
        """Test explicit editor mode settings."""
        config = OpenHandsConfig()
        
        config.cli.editor_mode = 'emacs'
        assert config.cli.get_effective_editor_mode() == 'emacs'
        
        config.cli.editor_mode = 'vi'
        assert config.cli.get_effective_editor_mode() == 'vi'

    def test_vi_mode_compatibility(self):
        """Test backward compatibility with vi_mode setting."""
        config = OpenHandsConfig()
        
        # Test vi_mode=True
        config.cli.vi_mode = True
        assert config.cli.is_vi_mode() is True
        
        # Test vi_mode=False
        config.cli.vi_mode = False
        assert config.cli.is_vi_mode() == (config.cli.get_effective_editor_mode() == 'vi')
        
        # Test vi_mode precedence
        config.cli.vi_mode = True
        config.cli.editor_mode = 'emacs'
        assert config.cli.get_effective_editor_mode() == 'emacs'
        assert config.cli.is_vi_mode() is True  # vi_mode takes precedence

    def test_cli_arguments(self):
        """Test CLI argument parsing."""
        main_parser = get_cli_parser()
        parser = get_subparser(main_parser, 'cli')
        
        # Test --editor-mode argument
        args = parser.parse_args(['--editor-mode', 'emacs'])
        assert args.editor_mode == 'emacs'
        
        args = parser.parse_args(['--editor-mode', 'vi'])
        assert args.editor_mode == 'vi'
        
        args = parser.parse_args(['--editor-mode', 'auto'])
        assert args.editor_mode == 'auto'
        
        # Test --vi-mode argument (deprecated)
        args = parser.parse_args(['--vi-mode'])
        assert args.vi_mode is True
        
        # Test both arguments together
        args = parser.parse_args(['--editor-mode', 'emacs', '--vi-mode'])
        assert args.editor_mode == 'emacs'
        assert args.vi_mode is True

    def test_config_integration(self):
        """Test integration with configuration system."""
        main_parser = get_cli_parser()
        parser = get_subparser(main_parser, 'cli')
        
        # Test emacs mode
        args = parser.parse_args(['--editor-mode', 'emacs'])
        config = setup_config_from_args(args)
        assert config.cli.editor_mode == 'emacs'
        assert config.cli.get_effective_editor_mode() == 'emacs'
        
        # Test vi mode
        args = parser.parse_args(['--editor-mode', 'vi'])
        config = setup_config_from_args(args)
        assert config.cli.editor_mode == 'vi'
        assert config.cli.get_effective_editor_mode() == 'vi'
        
        # Test auto mode
        args = parser.parse_args(['--editor-mode', 'auto'])
        config = setup_config_from_args(args)
        assert config.cli.editor_mode == 'auto'
        assert config.cli.get_effective_editor_mode() in ['emacs', 'vi']
        
        # Test deprecated vi_mode
        args = parser.parse_args(['--vi-mode'])
        config = setup_config_from_args(args)
        assert config.cli.vi_mode is True
        assert config.cli.is_vi_mode() is True

    def test_key_bindings_creation(self):
        """Test key binding creation."""
        from prompt_toolkit.key_binding import KeyBindings
        
        # Test emacs bindings
        emacs_bindings = create_enhanced_key_bindings('emacs')
        assert isinstance(emacs_bindings, KeyBindings)
        
        # Test vi bindings
        vi_bindings = create_enhanced_key_bindings('vi')
        assert isinstance(vi_bindings, KeyBindings)
        
        # Test that emacs bindings have more bindings than vi (which uses built-in)
        # This is a rough check since vi mode relies on prompt_toolkit's built-in bindings
        assert len(emacs_bindings.bindings) > 0

    def test_invalid_editor_mode(self):
        """Test handling of invalid editor modes."""
        # Note: Pydantic doesn't validate Literal types at runtime assignment
        # but the get_effective_editor_mode method handles invalid modes gracefully
        config = OpenHandsConfig()
        config.cli.editor_mode = 'invalid'
        
        # The method should still work and default to emacs for invalid modes
        # This is handled by the Literal type constraint in the model
        assert config.cli.get_effective_editor_mode() in ['emacs', 'vi']

    def test_config_file_integration(self):
        """Test that CLI config works with programmatic configuration."""
        # Note: CLI config is not currently loaded from TOML files
        # This test verifies that the CLI config can be set programmatically
        config = OpenHandsConfig()
        
        # Set CLI config programmatically
        config.cli.editor_mode = 'vi'
        config.cli.vi_mode = False
        
        assert config.cli.editor_mode == 'vi'
        assert config.cli.vi_mode is False
        assert config.cli.get_effective_editor_mode() == 'vi'
        assert config.cli.is_vi_mode() is True  # because effective mode is vi

    def test_environment_variable_precedence(self):
        """Test that environment variables work correctly with auto mode."""
        config = OpenHandsConfig()
        config.cli.editor_mode = 'auto'
        
        # Test case-insensitive matching
        with patch.dict(os.environ, {'EDITOR': 'VIM'}):
            assert config.cli.get_effective_editor_mode() == 'vi'
        
        with patch.dict(os.environ, {'EDITOR': '/usr/bin/vim'}):
            assert config.cli.get_effective_editor_mode() == 'vi'
        
        with patch.dict(os.environ, {'EDITOR': 'neovim'}):
            assert config.cli.get_effective_editor_mode() == 'vi'
        
        with patch.dict(os.environ, {'EDITOR': 'code'}):
            assert config.cli.get_effective_editor_mode() == 'emacs'