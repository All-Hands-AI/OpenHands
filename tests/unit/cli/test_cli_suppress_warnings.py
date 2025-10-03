"""Test warning suppression functionality in CLI mode."""

import warnings
from io import StringIO
from unittest.mock import patch

from openhands.cli.suppress_warnings import suppress_cli_warnings


class TestWarningSuppressionCLI:
    """Test cases for CLI warning suppression."""

    def test_suppress_pydantic_warnings(self):
        """Test that Pydantic serialization warnings are suppressed."""
        # Apply suppression
        suppress_cli_warnings()

        # Capture stderr to check if warnings are printed
        captured_output = StringIO()
        with patch('sys.stderr', captured_output):
            # Trigger Pydantic serialization warning
            warnings.warn(
                'Pydantic serializer warnings: PydanticSerializationUnexpectedValue',
                UserWarning,
                stacklevel=2,
            )

        # Should be suppressed (no output to stderr)
        output = captured_output.getvalue()
        assert 'Pydantic serializer warnings' not in output

    def test_suppress_deprecated_method_warnings(self):
        """Test that deprecated method warnings are suppressed."""
        # Apply suppression
        suppress_cli_warnings()

        # Capture stderr to check if warnings are printed
        captured_output = StringIO()
        with patch('sys.stderr', captured_output):
            # Trigger deprecated method warning
            warnings.warn(
                'Call to deprecated method get_events. (Use search_events instead)',
                DeprecationWarning,
                stacklevel=2,
            )

        # Should be suppressed (no output to stderr)
        output = captured_output.getvalue()
        assert 'deprecated method' not in output

    def test_suppress_expected_fields_warnings(self):
        """Test that expected fields warnings are suppressed."""
        # Apply suppression
        suppress_cli_warnings()

        # Capture stderr to check if warnings are printed
        captured_output = StringIO()
        with patch('sys.stderr', captured_output):
            # Trigger expected fields warning
            warnings.warn(
                'Expected 9 fields but got 5: Expected `Message`',
                UserWarning,
                stacklevel=2,
            )

        # Should be suppressed (no output to stderr)
        output = captured_output.getvalue()
        assert 'Expected 9 fields' not in output

    def test_regular_warnings_not_suppressed(self):
        """Test that regular warnings are NOT suppressed."""
        # Apply suppression
        suppress_cli_warnings()

        # Capture stderr to check if warnings are printed
        captured_output = StringIO()
        with patch('sys.stderr', captured_output):
            # Trigger a regular warning that should NOT be suppressed
            warnings.warn(
                'This is a regular warning that should appear',
                UserWarning,
                stacklevel=2,
            )

        # Should NOT be suppressed (should appear in stderr)
        output = captured_output.getvalue()
        assert 'regular warning' in output

    def test_module_import_applies_suppression(self):
        """Test that importing the module automatically applies suppression."""
        # Reset warnings filters
        warnings.resetwarnings()

        # Re-import the module to trigger suppression again
        import importlib

        import openhands.cli.suppress_warnings

        importlib.reload(openhands.cli.suppress_warnings)

        # Capture stderr to check if warnings are printed
        captured_output = StringIO()
        with patch('sys.stderr', captured_output):
            warnings.warn(
                'Pydantic serializer warnings: test', UserWarning, stacklevel=2
            )

        # Should be suppressed (no output to stderr)
        output = captured_output.getvalue()
        assert 'Pydantic serializer warnings' not in output

    def test_warning_filters_are_applied(self):
        """Test that warning filters are properly applied."""
        # Reset warnings filters
        warnings.resetwarnings()

        # Apply suppression
        suppress_cli_warnings()

        # Check that filters are in place
        filters = warnings.filters

        # Should have filters for the specific warning patterns
        filter_messages = [f[1] for f in filters if f[1] is not None]

        # Check that our specific patterns are in the filters
        assert any(
            'Pydantic serializer warnings' in str(msg) for msg in filter_messages
        )
        assert any('deprecated method' in str(msg) for msg in filter_messages)
