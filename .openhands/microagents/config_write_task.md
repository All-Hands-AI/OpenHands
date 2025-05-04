# Status: Implementing User Configuration Persistence

This PR implements a new configuration persistence system that allows saving user-specific settings to a dedicated TOML file (`~/.openhands/config.toml`), while keeping secrets in a separate JSON file (`~/.openhands/secrets.json`). This split architecture provides better separation of concerns and more appropriate storage formats for each type of data.

## Current Status

### Completed
1. **Core TOML Writing Mechanism**
   * Implemented `save_setting_to_user_toml` in `config_save.py` with comprehensive validation and error handling
   * Added snapshot mechanism to track TOML-sourced values vs. env/cli overrides
   * Implemented helpers for safe value access and default value retrieval
   * Added extensive unit tests covering all key scenarios

2. **Settings Store Integration**
   * Updated `FileSettingsStore` to use the new TOML writing mechanism
   * Implemented mapping between Settings model and AppConfig paths
   * Added unit tests for store operations

3. **Secrets Handling**
   * Secrets (API keys, tokens) are now stored separately in `secrets.json`
   * Implemented `FileSecretsStore` for dedicated secrets management
   * Secrets remain in JSON format for better compatibility with existing code

### Remaining Tasks
1. **Runtime Config Updates**
   * Implement mechanism to update runtime `AppConfig` instance when settings change
   * Add callbacks or direct access to global config object
   * Add tests for runtime updates

2. **CLI Integration**
   * Add CLI commands for viewing/modifying user TOML settings
   * Ensure CLI respects the same validation rules as the API
   * Add CLI integration tests

3. **Documentation & Cleanup**
   * Update configuration documentation to reflect the new architecture
   * Document the split between settings (TOML) and secrets (JSON)
   * Remove references to old `settings.json` mechanism


