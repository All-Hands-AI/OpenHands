# Plan: Implement Saving Configuration to User TOML

This plan outlines the steps to refactor the configuration system to allow saving user-specific settings to a dedicated TOML file (`~/.openhands/config.toml`), replacing the previous `settings.json` mechanism used by the web UI and addressing inconsistencies between UI and CLI configuration persistence.

## Overall Plan Phases

1.  **Phase 1: Core TOML Writing Mechanism & Unit Tests**
    *   Implement the core logic for writing specific configuration values to the user's TOML file (`~/.openhands/config.toml`), respecting the configuration layering (defaults, project TOML, user TOML, env, cli) and using `tomlkit` to preserve structure. This includes the snapshot mechanism and potentially modular `update_toml_section` methods within config classes. Create comprehensive unit tests.
2.  **Phase 2: Integrate Saving into `FileSettingsStore`**
    *   Modify the existing `FileSettingsStore` (the OSS implementation of the settings storage) to use the new core TOML writing mechanism developed in Phase 1, replacing the old `settings.json` logic. Update its `load` method accordingly. Update related unit tests.
3.  **Phase 3: Refactor Settings API Endpoint & Secrets Handling**
    *   Adapt the `/api/settings` endpoint to work seamlessly with the modified `FileSettingsStore`. Finalize and implement the strategy for handling secrets (either within the user TOML or a separate store). Update API tests.
4.  **Phase 4: CLI Integration & Runtime Update**
    *   Integrate the saving mechanism into any relevant CLI commands. Implement the logic to update the *runtime* `AppConfig` instance immediately after a setting is saved, ensuring changes take effect without a restart. Add CLI/integration tests.
5.  **Phase 5: Documentation & Cleanup**
    *   Update all relevant documentation regarding configuration files and management. Remove old/obsolete code related to `.openhands.toml` and `settings.json`.

## Phase 1 Detailed Steps

1.  **Dependency:**
    *   Add `tomlkit` to `[tool.poetry.dependencies]` in `pyproject.toml`.
2.  **User Config Path:**
    *   Define a standard location in `openhands/core/config/utils.py` or `constants.py`:
        ```python
        from pathlib import Path
        USER_CONFIG_DIR = Path.home() / '.openhands'
        USER_CONFIG_PATH = USER_CONFIG_DIR / 'config.toml'
        ```
    *   Ensure `USER_CONFIG_DIR` is created if it doesn't exist during config loading or saving (e.g., using `USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)`).
3.  **Snapshot Logic (`openhands/core/config/utils.py`):**
    *   Modify `load_app_config`:
        *   Load project `config.toml` into `config = AppConfig()`.
        *   Attempt to load `USER_CONFIG_PATH` using `load_from_toml(config, USER_CONFIG_PATH)`. Handle `FileNotFoundError` gracefully.
        *   Create `toml_config_snapshot = config.model_copy(deep=True)`. **This snapshot represents the state after TOMLs but before Env/CLI.**
        *   Continue with `load_from_env(config, os.environ)`.
        *   Return both `config` and `toml_config_snapshot` (e.g., as a tuple or a simple container object). The application needs access to both.
    *   Modify `setup_config_from_args` to accept and potentially modify the `config` object while being aware of the `toml_config_snapshot`. It should return both as well.
4.  **Central Save Function (`openhands/core/config/utils.py` or new file `config_save.py`):**
    *   Create `save_setting_to_user_toml(app_config: AppConfig, snapshot: AppConfig, setting_path: str, new_value: Any) -> bool`:
        *   `setting_path` is dot-notation (e.g., `'llm.model'`, `'sandbox.timeout'`).
        *   Returns `True` if the value was written to TOML, `False` otherwise.
        *   Inside:
            *   Ensure `USER_CONFIG_DIR` exists.
            *   Load `USER_CONFIG_PATH` using `tomlkit.load()`. Handle `FileNotFoundError` by creating an empty `tomlkit.document()`. Let's call it `user_toml_doc`.
            *   Navigate `user_toml_doc`, `app_config`, and `snapshot` using `setting_path` to find the target section/key and corresponding values (`runtime_value`, `snapshot_value`). Handle nested paths.
            *   Get the Pydantic default for the specific field using `setting_path`.
            *   **Decision Logic:**
                *   If `new_value == runtime_value`: No change requested, return `False`.
                *   If `runtime_value != snapshot_value`: Current value is overridden by Env/CLI. Log warning, return `False` (do not save).
                *   If `new_value == pydantic_default`: User is setting it back to default. Consider *removing* the key from `user_toml_doc` if it exists. Return `True` if removed/already absent.
                *   Otherwise (`new_value` is different, runtime value came from TOML/default, `new_value` is not default): Update the `user_toml_doc` at the specific key using `tomlkit`'s API (e.g., `section[key] = new_value`). Return `True`.
            *   Use `tomlkit.dump()` to write the modified `user_toml_doc` back to `USER_CONFIG_PATH`.
            *   **Add TODO Comment:**
                ```python
                # TODO: Update the runtime app_config instance with the new_value
                #       so the change takes effect immediately without restart.
                #       This needs careful handling, potentially involving callbacks
                #       or direct access to the global config object.
                ```
5.  **Modular Writing Method (Optional Refinement):**
    *   While the central function handles the core logic, individual config classes (`LLMConfig`, `SandboxConfig`) could provide helper methods to map their fields to TOML paths or perform type-specific serialization if needed, called by the central function. This keeps the central function cleaner.
    *   Example: `LLMConfig.update_toml_section(self, toml_section, snapshot_section)` could iterate its fields and update the `toml_section` based on the comparison logic, called by a broader `save_user_config(app_config, snapshot)` function. (Consider if this adds too much complexity vs. the central function with dot-notation paths).
6.  **Unit Tests (`tests/unit/test_config_write.py`):**
    *   Create the file.
    *   Use `pytest` and `unittest.mock`.
    *   Mock file system operations (`Path.home`, `open`, `tomlkit.load`, `tomlkit.dump`, `Path.mkdir`) using `patch`.
    *   Use `tmp_path` fixture for temporary config files.
    *   Test `load_app_config` correctly creates and returns the snapshot alongside the final config.
    *   Test `save_setting_to_user_toml`:
        *   Saving a valid change.
        *   Not saving when overridden by env/cli.
        *   Removing key when set back to default.
        *   Correctly creating/updating nested sections (e.g., saving `llm.model`).
        *   Handling `USER_CONFIG_PATH` not existing initially.
        *   Preserving other values/comments in the TOML file (requires writing a sample file with comments to `tmp_path` and verifying it's preserved after save).
