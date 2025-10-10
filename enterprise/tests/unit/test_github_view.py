from unittest import TestCase, mock

from integrations.github.github_view import GithubFactory, get_oh_labels
from integrations.models import Message, SourceType


class TestGithubLabels(TestCase):
    def test_labels_with_staging(self):
        oh_label, inline_oh_label = get_oh_labels('staging.all-hands.dev')
        self.assertEqual(oh_label, 'openhands-exp')
        self.assertEqual(inline_oh_label, '@openhands-exp')

    def test_labels_with_staging_v2(self):
        oh_label, inline_oh_label = get_oh_labels('main.staging.all-hands.dev')
        self.assertEqual(oh_label, 'openhands-exp')
        self.assertEqual(inline_oh_label, '@openhands-exp')

    def test_labels_with_local(self):
        oh_label, inline_oh_label = get_oh_labels('localhost:3000')
        self.assertEqual(oh_label, 'openhands-exp')
        self.assertEqual(inline_oh_label, '@openhands-exp')

    def test_labels_with_prod(self):
        oh_label, inline_oh_label = get_oh_labels('app.all-hands.dev')
        self.assertEqual(oh_label, 'openhands')
        self.assertEqual(inline_oh_label, '@openhands')

    def test_labels_with_spaces(self):
        """Test that spaces are properly stripped"""
        oh_label, inline_oh_label = get_oh_labels('  local  ')
        self.assertEqual(oh_label, 'openhands-exp')
        self.assertEqual(inline_oh_label, '@openhands-exp')


class TestGithubCommentCaseInsensitivity(TestCase):
    @mock.patch('integrations.github.github_view.INLINE_OH_LABEL', '@openhands')
    def test_issue_comment_case_insensitivity(self):
        # Test with lowercase mention
        message_lower = Message(
            source=SourceType.GITHUB,
            message={
                'payload': {
                    'action': 'created',
                    'comment': {'body': 'hello @openhands please help'},
                    'issue': {'number': 1},
                }
            },
        )

        # Test with uppercase mention
        message_upper = Message(
            source=SourceType.GITHUB,
            message={
                'payload': {
                    'action': 'created',
                    'comment': {'body': 'hello @OPENHANDS please help'},
                    'issue': {'number': 1},
                }
            },
        )

        # Test with mixed case mention
        message_mixed = Message(
            source=SourceType.GITHUB,
            message={
                'payload': {
                    'action': 'created',
                    'comment': {'body': 'hello @OpenHands please help'},
                    'issue': {'number': 1},
                }
            },
        )

        # All should be detected as issue comments with mentions
        self.assertTrue(GithubFactory.is_issue_comment(message_lower))
        self.assertTrue(GithubFactory.is_issue_comment(message_upper))
        self.assertTrue(GithubFactory.is_issue_comment(message_mixed))
