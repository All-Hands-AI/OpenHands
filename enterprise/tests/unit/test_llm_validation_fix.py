"""
Unit tests for the LLM settings validation bug fix.

These tests verify that the validate_llm_settings_changes function correctly
identifies only the LLM settings that are actually being changed, not just
settings that differ from defaults.
"""

from pydantic import SecretStr

from server.utils.subscription import validate_llm_settings_changes
from openhands.storage.data_models.settings import Settings


def test_validate_llm_settings_changes_with_no_changes():
    """Test that no LLM settings are flagged when nothing is changed."""
    # User's current settings
    current_settings = Settings(
        language='en',
        agent='CodeActAgent',
        llm_model='gpt-4',
        confirmation_mode=True,
        search_api_key=SecretStr('search-key'),
        max_iterations=50,
    ).model_dump()

    # Request with same settings (no changes)
    request_settings = {
        'language': 'en',
        'agent': 'CodeActAgent',
        'llm_model': 'gpt-4',
        'confirmation_mode': True,
        'search_api_key': 'search-key',
        'max_iterations': 50,
    }

    changed_llm_settings = validate_llm_settings_changes(request_settings, current_settings)

    assert changed_llm_settings == [], f"Expected no changes, got: {changed_llm_settings}"


def test_validate_llm_settings_changes_with_non_llm_changes_only():
    """Test that only non-LLM changes don't flag any LLM settings."""
    # User's current settings
    current_settings = Settings(
        language='en',
        agent='CodeActAgent',
        llm_model='gpt-4',
        confirmation_mode=True,
        search_api_key=SecretStr('search-key'),
        max_iterations=50,
        user_consents_to_analytics=False,
    ).model_dump()

    # Request with non-LLM changes only
    request_settings = {
        'language': 'es',  # Changed (non-LLM)
        'agent': 'CodeActAgent',  # Same (LLM)
        'llm_model': 'gpt-4',  # Same (LLM)
        'confirmation_mode': True,  # Same (LLM)
        'search_api_key': 'search-key',  # Same (LLM)
        'max_iterations': 100,  # Changed (non-LLM)
        'user_consents_to_analytics': True,  # Changed (non-LLM)
    }

    changed_llm_settings = validate_llm_settings_changes(request_settings, current_settings)

    assert changed_llm_settings == [], f"Expected no LLM changes, got: {changed_llm_settings}"


def test_validate_llm_settings_changes_with_llm_changes():
    """Test that LLM changes are correctly identified."""
    # User's current settings
    current_settings = Settings(
        language='en',
        agent='CodeActAgent',
        llm_model='gpt-4',
        confirmation_mode=True,
        search_api_key=SecretStr('search-key'),
        max_iterations=50,
    ).model_dump()

    # Request with LLM changes
    request_settings = {
        'language': 'es',  # Changed (non-LLM)
        'agent': 'PlannerAgent',  # Changed (LLM)
        'llm_model': 'gpt-3.5-turbo',  # Changed (LLM)
        'confirmation_mode': True,  # Same (LLM)
        'search_api_key': 'search-key',  # Same (LLM)
        'max_iterations': 100,  # Changed (non-LLM)
    }

    changed_llm_settings = validate_llm_settings_changes(request_settings, current_settings)

    expected_changes = ['agent', 'llm_model']
    assert set(changed_llm_settings) == set(expected_changes), (
        f"Expected {expected_changes}, got: {changed_llm_settings}"
    )


def test_validate_llm_settings_changes_with_confirmation_mode_change():
    """Test that confirmation_mode changes are detected."""
    # User's current settings
    current_settings = Settings(
        confirmation_mode=False,
        agent='CodeActAgent',
    ).model_dump()

    # Request with confirmation_mode change
    request_settings = {
        'confirmation_mode': True,  # Changed (LLM)
        'agent': 'CodeActAgent',  # Same (LLM)
    }

    changed_llm_settings = validate_llm_settings_changes(request_settings, current_settings)

    assert changed_llm_settings == ['confirmation_mode'], (
        f"Expected ['confirmation_mode'], got: {changed_llm_settings}"
    )


def test_validate_llm_settings_changes_with_search_api_key_change():
    """Test that search_api_key changes are detected."""
    # User's current settings
    current_settings = Settings(
        search_api_key=SecretStr('old-key'),
        agent='CodeActAgent',
    ).model_dump()

    # Request with search_api_key change
    request_settings = {
        'search_api_key': 'new-key',  # Changed (LLM)
        'agent': 'CodeActAgent',  # Same (LLM)
    }

    changed_llm_settings = validate_llm_settings_changes(request_settings, current_settings)

    assert changed_llm_settings == ['search_api_key'], (
        f"Expected ['search_api_key'], got: {changed_llm_settings}"
    )


def test_validate_llm_settings_changes_new_user_scenario():
    """Test the scenario where a new user has no existing settings."""
    # No current settings (new user)
    current_settings = None

    # Request with frontend default values
    request_settings = {
        'language': 'en',
        'agent': 'CodeActAgent',  # LLM setting from frontend defaults
        'llm_model': 'openhands/claude-sonnet-4-20250514',  # LLM setting from frontend defaults
        'confirmation_mode': False,  # LLM setting from frontend defaults
        'search_api_key': '',  # LLM setting from frontend defaults
        'max_iterations': 50,  # Non-LLM setting
    }

    changed_llm_settings = validate_llm_settings_changes(request_settings, current_settings)

    # For new users, all LLM settings in the request should be flagged as changes
    expected_changes = ['agent', 'llm_model', 'confirmation_mode', 'search_api_key']
    assert set(changed_llm_settings) == set(expected_changes), (
        f"Expected {expected_changes}, got: {changed_llm_settings}"
    )


def test_validate_llm_settings_changes_reproduces_original_bug():
    """
    Test that reproduces the original bug scenario.

    This test demonstrates what the old validation logic would have done wrong,
    and verifies that the new logic handles it correctly.
    """
    # User's current settings (they have LLM settings configured)
    current_settings = Settings(
        language='en',
        agent='CodeActAgent',
        llm_model='gpt-4',
        confirmation_mode=True,
        search_api_key=SecretStr('existing-key'),
        max_iterations=50,
    ).model_dump()

    # Frontend sends entire settings object with only language changed
    request_settings = {
        'language': 'es',  # Changed (non-LLM)
        'agent': 'CodeActAgent',  # Same as current (LLM)
        'llm_model': 'gpt-4',  # Same as current (LLM)
        'confirmation_mode': True,  # Same as current (LLM)
        'search_api_key': 'existing-key',  # Same as current (LLM)
        'max_iterations': 50,  # Same as current (non-LLM)
    }

    # With the fix: should detect no LLM changes
    changed_llm_settings = validate_llm_settings_changes(request_settings, current_settings)
    assert changed_llm_settings == [], (
        f"Bug fix failed: Expected no LLM changes, got: {changed_llm_settings}"
    )

    # Simulate old buggy behavior (comparing against defaults)
    default_settings = Settings().model_dump()  # All None values
    changed_llm_settings_old_bug = validate_llm_settings_changes(request_settings, default_settings)

    # Old behavior would have flagged these as changes because they differ from None
    expected_old_bug_result = ['agent', 'llm_model', 'confirmation_mode', 'search_api_key']
    assert set(changed_llm_settings_old_bug) == set(expected_old_bug_result), (
        f"Old bug simulation failed: Expected {expected_old_bug_result}, got: {changed_llm_settings_old_bug}"
    )

    print("✅ Bug fix verified: New logic correctly identifies no changes")
    print(f"❌ Old logic would have incorrectly flagged: {changed_llm_settings_old_bug}")


if __name__ == '__main__':
    # Run the tests manually if pytest is not available
    test_validate_llm_settings_changes_with_no_changes()
    test_validate_llm_settings_changes_with_non_llm_changes_only()
    test_validate_llm_settings_changes_with_llm_changes()
    test_validate_llm_settings_changes_with_confirmation_mode_change()
    test_validate_llm_settings_changes_with_search_api_key_change()
    test_validate_llm_settings_changes_new_user_scenario()
    test_validate_llm_settings_changes_reproduces_original_bug()
    print("✅ All tests passed!")
