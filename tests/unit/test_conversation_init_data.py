import pytest

from openhands.server.session.conversation_init_data import ConversationInitData


def test_provider_tokens_not_shared_between_instances():
    """Test that provider_tokens is not shared between instances."""
    # Create two instances
    instance1 = ConversationInitData()
    instance2 = ConversationInitData()

    # Verify they start with empty dictionaries
    assert instance1.provider_tokens == {}
    assert instance2.provider_tokens == {}

    # Modify the first instance
    instance1.provider_tokens["test_provider"] = "test_token"

    # Verify the second instance is not affected
    assert instance1.provider_tokens == {"test_provider": "test_token"}
    assert instance2.provider_tokens == {}


def test_selected_repository_not_shared_between_instances():
    """Test that selected_repository is not shared between instances."""
    # Create two instances
    instance1 = ConversationInitData()
    instance2 = ConversationInitData()

    # Verify they start with None
    assert instance1.selected_repository is None
    assert instance2.selected_repository is None

    # Modify the first instance
    instance1.selected_repository = "test_repo"

    # Verify the second instance is not affected
    assert instance1.selected_repository == "test_repo"
    assert instance2.selected_repository is None


def test_selected_branch_not_shared_between_instances():
    """Test that selected_branch is not shared between instances."""
    # Create two instances
    instance1 = ConversationInitData()
    instance2 = ConversationInitData()

    # Verify they start with None
    assert instance1.selected_branch is None
    assert instance2.selected_branch is None

    # Modify the first instance
    instance1.selected_branch = "test_branch"

    # Verify the second instance is not affected
    assert instance1.selected_branch == "test_branch"
    assert instance2.selected_branch is None