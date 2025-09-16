import json
from unittest.mock import MagicMock, patch
from openhands_cli.tui.settings.settings_screen import SettingsScreen
from pathlib import Path

from openhands.sdk import LLM, Conversation
from openhands_cli.user_actions.settings_action import SettingsType
from pydantic import SecretStr
import pytest
from openhands_cli.agent_chat import run_cli_entry


def read_json(path: Path) -> dict:
    with open(path, "r") as f:
        return json.load(f)

def make_screen_with_conversation(model="openai/gpt-4o-mini", api_key="sk-xyz"):
    llm = LLM(model=model, api_key=SecretStr(api_key))
    # Conversation(agent) signature may vary across versions; adapt if needed:
    from openhands.sdk.agent import Agent
    agent = Agent(llm=llm, tools=[])
    conv = Conversation(agent)
    return SettingsScreen(conversation=conv)

def seed_file(path: Path, model: str = "openai/gpt-4o-mini", api_key: str = "sk-old"):
    path.parent.mkdir(parents=True, exist_ok=True)
    LLM(model=model, api_key=SecretStr(api_key)).store_to_json(str(path))



def test_llm_settings_save_and_load(tmp_path: Path):
    """Round-trip persistence via store_to_json and reading file back."""
    settings_path = tmp_path / "llm_settings.json"
    screen = SettingsScreen(conversation=None)

    with patch("openhands_cli.tui.settings.settings_screen.FULL_LLM_SETTINGS_PATH", str(settings_path)):
        screen._save_llm_settings(provider="openai", model="gpt-4o-mini", api_key="sk-test-123")

    assert settings_path.exists(), "settings file should be created"

    data = read_json(settings_path)

    # Minimal, schema-agnostic checks:
    assert data.get("model") == "openai/gpt-4o-mini"
    assert "api_key" in data and isinstance(data["api_key"], str) and data["api_key"], "api_key should be persisted"

    llm = LLM.load_from_json(settings_path)
    assert llm.model == "openai/gpt-4o-mini"


def test_first_time_setup_workflow(tmp_path: Path):
    settings_path = tmp_path / "llm_settings.json"
    # screen = make_screen_with_conversation(model="unknown/placeholder", api_key="sk-initial")
    screen = SettingsScreen()

    with (
        patch("openhands_cli.tui.settings.settings_screen.FULL_LLM_SETTINGS_PATH", str(settings_path)),
        patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation", return_value=SettingsType.BASIC),
        patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider", return_value="openai"),
        patch("openhands_cli.tui.settings.settings_screen.choose_llm_model", return_value="gpt-4o-mini"),
        patch("openhands_cli.tui.settings.settings_screen.prompt_api_key", return_value="sk-first"),
        patch("openhands_cli.tui.settings.settings_screen.save_settings_confirmation", return_value=True),
    ):
        screen.configure_settings()

    data = read_json(settings_path)
    assert data.get("model") == "openai/gpt-4o-mini"
    assert data.get("api_key") == "sk-first"


def test_update_existing_settings_workflow(tmp_path: Path):
    settings_path = tmp_path / "llm_settings.json"
    seed_file(settings_path, model="openai/gpt-4o-mini", api_key="sk-old")
    screen = make_screen_with_conversation(model="openai/gpt-4o-mini", api_key="sk-old")

    with (
        patch("openhands_cli.tui.settings.settings_screen.FULL_LLM_SETTINGS_PATH", str(settings_path)),
        patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation", return_value=SettingsType.BASIC),
        patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider", return_value="anthropic"),
        patch("openhands_cli.tui.settings.settings_screen.choose_llm_model", return_value="claude-3-5-sonnet"),
        patch("openhands_cli.tui.settings.settings_screen.prompt_api_key", return_value="sk-updated"),
        patch("openhands_cli.tui.settings.settings_screen.save_settings_confirmation", return_value=True),
    ):
        screen.configure_settings()

    data = read_json(settings_path)
    assert data.get("model") == "anthropic/claude-3-5-sonnet"
    assert data.get("api_key") == "sk-updated"


@pytest.mark.parametrize(
    "step_to_cancel",
    ["type", "provider", "model", "apikey", "save"],
)
def test_workflow_cancellation_at_each_step(tmp_path: Path, step_to_cancel: str):
    settings_path = tmp_path / "llm_settings.json"
    screen = make_screen_with_conversation()

    # Base happy-path patches
    patches = {
        "settings_type_confirmation": MagicMock(return_value=SettingsType.BASIC),
        "choose_llm_provider": MagicMock(return_value="openai"),
        "choose_llm_model": MagicMock(return_value="gpt-4o-mini"),
        "prompt_api_key": MagicMock(return_value="sk-new"),
        "save_settings_confirmation": MagicMock(return_value=True),
    }

    # Turn one step into a cancel
    if step_to_cancel == "type":
        patches["settings_type_confirmation"].side_effect = KeyboardInterrupt()
    elif step_to_cancel == "provider":
        patches["choose_llm_provider"].side_effect = KeyboardInterrupt()
    elif step_to_cancel == "model":
        patches["choose_llm_model"].side_effect = KeyboardInterrupt()
    elif step_to_cancel == "apikey":
        patches["prompt_api_key"].side_effect = KeyboardInterrupt()
    elif step_to_cancel == "save":
        patches["save_settings_confirmation"].side_effect = KeyboardInterrupt()

    with (
        patch("openhands_cli.tui.settings.settings_screen.FULL_LLM_SETTINGS_PATH", str(settings_path)),
        patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation", patches["settings_type_confirmation"]),
        patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider", patches["choose_llm_provider"]),
        patch("openhands_cli.tui.settings.settings_screen.choose_llm_model", patches["choose_llm_model"]),
        patch("openhands_cli.tui.settings.settings_screen.prompt_api_key", patches["prompt_api_key"]),
        patch("openhands_cli.tui.settings.settings_screen.save_settings_confirmation", patches["save_settings_confirmation"]),
    ):
        screen.configure_settings()

    # No file should be written on cancel
    assert not settings_path.exists(), f"settings file should not be written on cancel at '{step_to_cancel}'"

