import unittest

from openhands.server.session.conversation_init_data import ConversationInitData


class TestConversationInitData(unittest.TestCase):
    """Tests for the ConversationInitData class."""

    def test_provider_tokens_not_shared_between_instances(self):
        """Test that provider_tokens is not shared between instances."""
        # Create two instances
        instance1 = ConversationInitData()
        instance2 = ConversationInitData()

        # Verify they start with empty dictionaries
        self.assertEqual(instance1.provider_tokens, {})
        self.assertEqual(instance2.provider_tokens, {})

        # Modify the first instance
        instance1.provider_tokens["test_provider"] = "test_token"

        # Verify the second instance is not affected
        self.assertEqual(instance1.provider_tokens, {"test_provider": "test_token"})
        self.assertEqual(instance2.provider_tokens, {})

    def test_selected_repository_not_shared_between_instances(self):
        """Test that selected_repository is not shared between instances."""
        # Create two instances
        instance1 = ConversationInitData()
        instance2 = ConversationInitData()

        # Verify they start with None
        self.assertIsNone(instance1.selected_repository)
        self.assertIsNone(instance2.selected_repository)

        # Modify the first instance
        instance1.selected_repository = "test_repo"

        # Verify the second instance is not affected
        self.assertEqual(instance1.selected_repository, "test_repo")
        self.assertIsNone(instance2.selected_repository)

    def test_selected_branch_not_shared_between_instances(self):
        """Test that selected_branch is not shared between instances."""
        # Create two instances
        instance1 = ConversationInitData()
        instance2 = ConversationInitData()

        # Verify they start with None
        self.assertIsNone(instance1.selected_branch)
        self.assertIsNone(instance2.selected_branch)

        # Modify the first instance
        instance1.selected_branch = "test_branch"

        # Verify the second instance is not affected
        self.assertEqual(instance1.selected_branch, "test_branch")
        self.assertIsNone(instance2.selected_branch)


if __name__ == "__main__":
    unittest.main()