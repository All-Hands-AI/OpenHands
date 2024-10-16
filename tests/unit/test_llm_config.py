import pathlib

import pytest

from openhands.core.config import AppConfig
from openhands.core.config.utils import load_from_toml


@pytest.fixture
def default_config(monkeypatch):
    # Fixture to provide a default AppConfig instance
    yield AppConfig()


@pytest.fixture
def generic_llm_toml(tmp_path: pathlib.Path) -> str:
    """Fixture to create a generic LLM TOML configuration with all custom LLMs
    providing mandatory 'model' and 'api_key', and testing fallback to the generic section values
    for other attributes like 'num_retries'.
    """
    toml_content = """
[core]
workspace_base = "./workspace"

[llm]
model = "base-model"
api_key = "base-api-key"
embedding_model = "base-embedding"
num_retries = 3

[llm.custom1]
model = "custom-model-1"
api_key = "custom-api-key-1"
# 'num_retries' is not overridden and should fallback to the value from [llm]

[llm.custom2]
model = "custom-model-2"
api_key = "custom-api-key-2"
num_retries = 5  # Overridden value

[llm.custom3]
model = "custom-model-3"
api_key = "custom-api-key-3"
# No overrides for additional attributes
    """
    toml_file = tmp_path / 'llm_config.toml'
    toml_file.write_text(toml_content)
    return str(toml_file)


def test_load_from_toml_llm_with_fallback(
    default_config: AppConfig, generic_llm_toml: str
) -> None:
    """Test that custom LLM configurations fallback non-overridden attributes
    like 'num_retries' from the generic [llm] section.
    """
    load_from_toml(default_config, generic_llm_toml)

    # Verify generic LLM configuration
    generic_llm = default_config.get_llm_config('llm')
    assert generic_llm.model == 'base-model'
    assert generic_llm.api_key == 'base-api-key'
    assert generic_llm.embedding_model == 'base-embedding'
    assert generic_llm.num_retries == 3

    # Verify custom1 LLM falls back 'num_retries' from base
    custom1 = default_config.get_llm_config('custom1')
    assert custom1.model == 'custom-model-1'
    assert custom1.api_key == 'custom-api-key-1'
    assert custom1.embedding_model == 'base-embedding'
    assert custom1.num_retries == 3  # from [llm]

    # Verify custom2 LLM overrides 'num_retries'
    custom2 = default_config.get_llm_config('custom2')
    assert custom2.model == 'custom-model-2'
    assert custom2.api_key == 'custom-api-key-2'
    assert custom2.embedding_model == 'base-embedding'
    assert custom2.num_retries == 5  # overridden value

    # Verify custom3 LLM inherits all attributes except 'model' and 'api_key'
    custom3 = default_config.get_llm_config('custom3')
    assert custom3.model == 'custom-model-3'
    assert custom3.api_key == 'custom-api-key-3'
    assert custom3.embedding_model == 'base-embedding'
    assert custom3.num_retries == 3  # from [llm]


def test_load_from_toml_llm_custom_overrides_all(
    default_config: AppConfig, tmp_path: pathlib.Path
) -> None:
    """Test that a custom LLM can fully override all attributes from the generic [llm] section."""
    toml_content = """
[core]
workspace_base = "./workspace"

[llm]
model = "base-model"
api_key = "base-api-key"
embedding_model = "base-embedding"
num_retries = 3

[llm.custom_full]
model = "full-custom-model"
api_key = "full-custom-api-key"
embedding_model = "full-custom-embedding"
num_retries = 10
    """
    toml_file = tmp_path / 'full_override_llm.toml'
    toml_file.write_text(toml_content)

    load_from_toml(default_config, str(toml_file))

    # Verify generic LLM configuration remains unchanged
    generic_llm = default_config.get_llm_config('llm')
    assert generic_llm.model == 'base-model'
    assert generic_llm.api_key == 'base-api-key'
    assert generic_llm.embedding_model == 'base-embedding'
    assert generic_llm.num_retries == 3

    # Verify custom_full LLM overrides all attributes
    custom_full = default_config.get_llm_config('custom_full')
    assert custom_full.model == 'full-custom-model'
    assert custom_full.api_key == 'full-custom-api-key'
    assert custom_full.embedding_model == 'full-custom-embedding'
    assert custom_full.num_retries == 10  # overridden value


def test_load_from_toml_llm_custom_partial_override(
    default_config: AppConfig, generic_llm_toml: str
) -> None:
    """Test that custom LLM configurations can partially override attributes
    from the generic [llm] section while inheriting others.
    """
    load_from_toml(default_config, generic_llm_toml)

    # Verify custom1 LLM overrides 'model' and 'api_key' but inherits 'num_retries'
    custom1 = default_config.get_llm_config('custom1')
    assert custom1.model == 'custom-model-1'
    assert custom1.api_key == 'custom-api-key-1'
    assert custom1.embedding_model == 'base-embedding'
    assert custom1.num_retries == 3  # from [llm]

    # Verify custom2 LLM overrides 'model', 'api_key', and 'num_retries'
    custom2 = default_config.get_llm_config('custom2')
    assert custom2.model == 'custom-model-2'
    assert custom2.api_key == 'custom-api-key-2'
    assert custom2.embedding_model == 'base-embedding'
    assert custom2.num_retries == 5  # Overridden value


def test_load_from_toml_llm_custom_no_override(
    default_config: AppConfig, generic_llm_toml: str
) -> None:
    """Test that custom LLM configurations with no additional overrides
    inherit all non-specified attributes from the generic [llm] section.
    """
    load_from_toml(default_config, generic_llm_toml)

    # Verify custom3 LLM inherits 'embedding_model' and 'num_retries' from generic
    custom3 = default_config.get_llm_config('custom3')
    assert custom3.model == 'custom-model-3'
    assert custom3.api_key == 'custom-api-key-3'
    assert custom3.embedding_model == 'base-embedding'
    assert custom3.num_retries == 3  # from [llm]


def test_load_from_toml_llm_missing_generic(
    default_config: AppConfig, tmp_path: pathlib.Path
) -> None:
    """Test that custom LLM configurations without a generic [llm] section
    use only their own attributes and fallback to defaults for others.
    """
    toml_content = """
[core]
workspace_base = "./workspace"

[llm.custom_only]
model = "custom-only-model"
api_key = "custom-only-api-key"
    """
    toml_file = tmp_path / 'custom_only_llm.toml'
    toml_file.write_text(toml_content)

    load_from_toml(default_config, str(toml_file))

    # Verify custom_only LLM uses its own attributes and defaults for others
    custom_only = default_config.get_llm_config('custom_only')
    assert custom_only.model == 'custom-only-model'
    assert custom_only.api_key == 'custom-only-api-key'
    assert custom_only.embedding_model == 'local'  # default value
    assert custom_only.num_retries == 8  # default value


def test_load_from_toml_llm_invalid_config(
    default_config: AppConfig, tmp_path: pathlib.Path
) -> None:
    """Test that invalid custom LLM configurations do not override the generic
    and raise appropriate warnings.
    """
    toml_content = """
[core]
workspace_base = "./workspace"

[llm]
model = "base-model"
api_key = "base-api-key"
num_retries = 3

[llm.invalid_custom]
unknown_attr = "should_not_exist"
    """
    toml_file = tmp_path / 'invalid_custom_llm.toml'
    toml_file.write_text(toml_content)

    load_from_toml(default_config, str(toml_file))

    # Verify generic LLM is loaded correctly
    generic_llm = default_config.get_llm_config('llm')
    assert generic_llm.model == 'base-model'
    assert generic_llm.api_key == 'base-api-key'
    assert generic_llm.num_retries == 3

    # Verify invalid_custom LLM does not override generic attributes
    custom_invalid = default_config.get_llm_config('invalid_custom')
    assert custom_invalid.model == 'base-model'
    assert custom_invalid.api_key == 'base-api-key'
    assert custom_invalid.num_retries == 3  # default value
    assert custom_invalid.embedding_model == 'local'  # default value
