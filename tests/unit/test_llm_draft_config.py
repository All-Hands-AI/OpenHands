import pathlib

import pytest

from openhands.core.config import AppConfig
from openhands.core.config.utils import load_from_toml


@pytest.fixture
def draft_llm_toml(tmp_path: pathlib.Path) -> str:
    toml_content = """
[core]
workspace_base = "./workspace"

[llm]
model = "base-model"
api_key = "base-api-key"
draft_editor = { model = "draft-model", api_key = "draft-api-key" }

[llm.custom1]
model = "custom-model-1"
api_key = "custom-api-key-1"
# Should use draft_editor from [llm] as fallback

[llm.custom2]
model = "custom-model-2"
api_key = "custom-api-key-2"
draft_editor = { model = "custom-draft", api_key = "custom-draft-key" }

[llm.custom3]
model = "custom-model-3"
api_key = "custom-api-key-3"
draft_editor = "null"  # Explicitly set to null in TOML
    """
    toml_file = tmp_path / 'llm_config.toml'
    toml_file.write_text(toml_content)
    return str(toml_file)


def test_draft_editor_fallback(draft_llm_toml):
    """Test that draft_editor is correctly handled in different scenarios:
    - Falls back to generic [llm] section value
    - Uses custom value when specified
    - Can be explicitly set to null
    """
    config = AppConfig()

    # Verify default draft_editor is None
    default_llm = config.get_llm_config('llm')
    assert default_llm.draft_editor is None

    # Load config from TOML
    load_from_toml(config, draft_llm_toml)

    # Verify generic LLM draft_editor
    generic_llm = config.get_llm_config('llm')
    assert generic_llm.draft_editor is not None
    assert generic_llm.draft_editor.model == 'draft-model'
    assert generic_llm.draft_editor.api_key == 'draft-api-key'

    # Verify custom1 uses draft_editor from generic as fallback
    custom1 = config.get_llm_config('custom1')
    assert custom1.model == 'custom-model-1'
    assert custom1.draft_editor is not None
    assert custom1.draft_editor.model == 'draft-model'
    assert custom1.draft_editor.api_key == 'draft-api-key'

    # Verify custom2 overrides draft_editor
    custom2 = config.get_llm_config('custom2')
    assert custom2.model == 'custom-model-2'
    assert custom2.draft_editor is not None
    assert custom2.draft_editor.model == 'custom-draft'
    assert custom2.draft_editor.api_key == 'custom-draft-key'

    # Verify custom3 has draft_editor explicitly set to None
    custom3 = config.get_llm_config('custom3')
    assert custom3.model == 'custom-model-3'
    assert custom3.draft_editor is None


def test_draft_editor_defaults(draft_llm_toml):
    """Test that draft_editor uses default values from LLMConfig when not specified"""
    config = AppConfig()
    load_from_toml(config, draft_llm_toml)

    generic_llm = config.get_llm_config('llm')
    assert generic_llm.draft_editor.num_retries == 8  # Default from LLMConfig
    assert generic_llm.draft_editor.embedding_model == 'local'  # Default from LLMConfig

    custom2 = config.get_llm_config('custom2')
    assert custom2.draft_editor.num_retries == 8  # Default from LLMConfig
    assert custom2.draft_editor.embedding_model == 'local'  # Default from LLMConfig
