
from unittest.mock import patch
from openhands_cli.agent_chat import run_cli_entry
import pytest


@patch("openhands_cli.agent_chat.print_formatted_text")
@patch("openhands_cli.tui.settings.settings_screen.save_settings_confirmation")
@patch("openhands_cli.tui.settings.settings_screen.prompt_api_key")
@patch("openhands_cli.tui.settings.settings_screen.choose_llm_model")
@patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider")
@patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation")
@pytest.mark.parametrize("interrupt_step", ["settings_type", "provider", "model", "api_key", "save"])
def test_first_time_users_can_escape_settings_flow_and_exit_app(
    mock_type,
    mock_provider,
    mock_model,
    mock_api_key,
    mock_save,
    mock_print,
    interrupt_step,
):
    """Test that KeyboardInterrupt is handled at each step of basic settings."""
    # Set up happy path defaults
    mock_type.return_value = 'basic'
    mock_provider.return_value = 'openai'
    mock_model.return_value = 'gpt-4o-mini'
    mock_api_key.return_value = 'sk-test'
    mock_save.return_value = True

    # Inject KeyboardInterrupt at the specified step
    if interrupt_step == 'settings_type':
        mock_type.side_effect = KeyboardInterrupt()
    elif interrupt_step == 'provider':
        mock_provider.side_effect = KeyboardInterrupt()
    elif interrupt_step == 'model':
        mock_model.side_effect = KeyboardInterrupt()
    elif interrupt_step == 'api_key':
        mock_api_key.side_effect = KeyboardInterrupt()
    elif interrupt_step == 'save':
        mock_save.side_effect = KeyboardInterrupt()

    run_cli_entry()
    calls = [call.args[0] for call in mock_print.call_args_list]
    assert any('Setup is required' in str(call) for call in calls)
    assert any('Goodbye!' in str(call) for call in calls)
