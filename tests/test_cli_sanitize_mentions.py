import pytest
from openhands.cli.tui import _sanitize_mentions_cli


class TestSanitizeMentionsCLI:
    def test_sanitizes_openhands_mention(self):
        text = "Hello @openhands world"
        result = _sanitize_mentions_cli(text)
        assert "@\u200Dopenhands" in result
        assert "@openhands" not in result

    def test_sanitizes_openhands_case_variants(self):
        text = "Hello @OpenHands and @OPENHANDS world"
        result = _sanitize_mentions_cli(text)
        assert "@\u200DOpenHands" in result
        assert "@\u200DOPENHANDS" in result

    def test_sanitizes_open_hands_variant(self):
        text = "Hello @open-hands world"
        result = _sanitize_mentions_cli(text)
        assert "@\u200Dopen-hands" in result
        assert "@open-hands" not in result

    def test_preserves_fenced_code_blocks(self):
        text = "```txt\n@openhands in code\n```"
        result = _sanitize_mentions_cli(text)
        assert "@openhands in code" in result
        assert "@\u200Dopenhands" not in result

    def test_sanitizes_outside_code_preserves_inside(self):
        text = "Before: @openhands\n```\n@openhands in code\n```\nAfter: @openhands"
        result = _sanitize_mentions_cli(text)
        # Should have both sanitized and unsanitized versions
        assert result.count("@\u200Dopenhands") == 2  # before and after
        assert "@openhands in code" in result  # inside code block

    def test_handles_multiple_code_blocks(self):
        text = "```\n@openhands\n```\nText: @openhands\n```\n@openhands\n```"
        result = _sanitize_mentions_cli(text)
        assert result.count("@\u200Dopenhands") == 1  # only in text
        assert result.count("@openhands") == 2  # in both code blocks

    def test_handles_empty_text(self):
        assert _sanitize_mentions_cli("") == ""
        assert _sanitize_mentions_cli(None) == ""

    def test_handles_text_without_mentions(self):
        text = "Hello world without mentions"
        result = _sanitize_mentions_cli(text)
        assert result == text

    def test_custom_blocklist(self):
        text = "Hello @custom and @openhands"
        result = _sanitize_mentions_cli(text, blocklist=["@custom"])
        assert "@\u200Dcustom" in result
        assert "@openhands" in result  # not in custom blocklist

    def test_case_insensitive_matching(self):
        text = "Hello @OPENHANDS world"
        result = _sanitize_mentions_cli(text, blocklist=["@openhands"])
        assert "@\u200DOPENHANDS" in result

    def test_handles_handles_without_at_prefix(self):
        text = "Hello openhands world"
        result = _sanitize_mentions_cli(text, blocklist=["openhands"])
        assert "@\u200Dopenhands" in result
