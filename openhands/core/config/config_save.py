import traceback
from typing import Any, Optional

import tomlkit
from pydantic import BaseModel

from openhands.core import logger
from openhands.core.config.app_config import AppConfig
from openhands.core.config.utils import USER_CONFIG_DIR, USER_CONFIG_PATH


def _get_value_from_path(obj: Any, path: str) -> Any:
    """Gets a value from a potentially nested object using dot notation."""
    keys = path.split('.')
    value = obj
    for key in keys:
        if isinstance(value, BaseModel):
            if hasattr(value, key):
                value = getattr(value, key)
            else:
                # Handle nested models like llms['llama3'].model
                if '.' in key and hasattr(value, key.split('.')[0]):
                    # This part needs refinement if we support saving nested dict items like llms
                    raise NotImplementedError(
                        f'Accessing nested dict items like {key} not fully implemented yet.'
                    )
                raise AttributeError(
                    f"Attribute '{key}' not found in object path '{path}'"
                )
        elif isinstance(value, dict):
            if key in value:
                value = value[key]
            else:
                raise KeyError(f"Key '{key}' not found in dict path '{path}'")
        else:
            raise TypeError(
                f'Cannot traverse path "{path}". Object is not a BaseModel or dict at key "{key}".'
            )
    return value


def _get_default_from_path(model: BaseModel, path: str) -> Any:
    """Gets the Pydantic default value for a field specified by dot notation."""
    keys = path.split('.')
    current_model = model
    field = None
    for i, key in enumerate(keys):
        if not isinstance(current_model, BaseModel):
            raise TypeError(f'Expected Pydantic model at path segment "{key}"')

        field = current_model.model_fields.get(key)
        if field is None:
            # Handle nested models like llms['llama3'].model - needs refinement
            raise AttributeError(
                f"Field '{key}' not found in model path '{path}'"
            )

        if i < len(keys) - 1:
            # If not the last key, get the nested model type
            # This assumes the field annotation is the nested model type
            nested_model_type = field.annotation
            if hasattr(nested_model_type, 'model_fields'):
                # Instantiate the nested model to access its defaults (if needed)
                # This might be inefficient if defaults are complex
                current_model = nested_model_type()
            else:
                raise TypeError(f'Field "{key}" is not a nested Pydantic model.')
        else:
            # Last key, get the default
            return field.get_default()
    # Should not be reached if path is valid
    return None


def _ensure_nested_tables(doc: tomlkit.TOMLDocument, path_keys: list[str]):
    """Ensures nested tables exist in the TOML document for a given path."""
    current_item = doc
    for i, key in enumerate(path_keys[:-1]):  # Iterate up to the second-to-last key
        if key not in current_item:
            current_item[key] = tomlkit.table()
            logger.openhands_logger.debug(f'Created table [{key}] in user TOML.')
        elif not isinstance(current_item[key], tomlkit.items.Table):
            raise TypeError(
                f'Expected a table at key "{key}", found {type(current_item[key])}. Cannot overwrite.'
            )
        current_item = current_item[key]
    return current_item


def save_setting_to_user_toml(
    app_config: AppConfig, setting_path: str, new_value: Any
) -> bool:
    """
    Saves a specific setting to the user's config TOML file (~/.openhands/config.toml).

    Args:
        app_config: The current runtime AppConfig instance (containing the snapshot).
        setting_path: The dot-notation path to the setting (e.g., 'llm.model', 'sandbox.timeout').
        new_value: The new value to save.

    Returns:
        True if the value was successfully saved or removed (if set to default),
        False otherwise (e.g., if overridden by env/cli or no change needed).
    """
    logger.openhands_logger.info(
        f"Attempting to save setting '{setting_path}' with value '{new_value}' to user TOML."
    )
    snapshot = app_config.get_toml_snapshot()
    if snapshot is None:
        logger.openhands_logger.error(
            'TOML snapshot not found in AppConfig. Cannot determine setting source.'
        )
        return False

    try:
        # Get values from runtime config, snapshot, and defaults
        runtime_value = _get_value_from_path(app_config, setting_path)
        snapshot_value = _get_value_from_path(snapshot, setting_path)
        pydantic_default = _get_default_from_path(AppConfig(), setting_path)

        logger.openhands_logger.debug(f"Runtime value: {runtime_value}")
        logger.openhands_logger.debug(f"Snapshot value: {snapshot_value}")
        logger.openhands_logger.debug(f"Pydantic default: {pydantic_default}")
        logger.openhands_logger.debug(f"New value: {new_value}")

        # Decision Logic
        if new_value == runtime_value:
            logger.openhands_logger.info(
                f"No change detected for '{setting_path}'. Skipping save."
            )
            return False  # No change needed

        if runtime_value != snapshot_value:
            logger.openhands_logger.warning(
                f"Setting '{setting_path}' is currently overridden by environment variable "
                f"or CLI argument (runtime: {runtime_value}, TOMLs: {snapshot_value}). "
                f"Change will not be persisted to user TOML file."
            )
            # TODO: Update runtime app_config instance if needed, even if not saving to TOML?
            #       This depends on desired behavior for UI changes vs env/cli overrides.
            #       For now, we only save if the source was TOML/default.
            return False

        # Ensure user config directory exists
        try:
            USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.openhands_logger.error(
                f"Failed to create user config directory {USER_CONFIG_DIR}: {e}"
            )
            return False

        # Load user TOML document
        try:
            with open(USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
                user_toml_doc = tomlkit.load(f)
            logger.openhands_logger.debug(f"Loaded user TOML: {USER_CONFIG_PATH}")
        except FileNotFoundError:
            user_toml_doc = tomlkit.document()
            logger.openhands_logger.debug(
                f"User TOML not found, creating new document: {USER_CONFIG_PATH}"
            )
        except Exception as e:
            logger.openhands_logger.error(
                f"Failed to load user TOML file {USER_CONFIG_PATH}: {e}\n{traceback.format_exc()}"
            )
            return False

        # Navigate and update/remove
        path_keys = setting_path.split('.')
        target_key = path_keys[-1]
        try:
            target_section = _ensure_nested_tables(user_toml_doc, path_keys)

            if new_value == pydantic_default:
                # Setting back to default: remove the key if it exists
                if target_key in target_section:
                    del target_section[target_key]
                    logger.openhands_logger.info(
                        f"Setting '{setting_path}' matches default. Removed from user TOML."
                    )
                    modified = True
                else:
                    logger.openhands_logger.info(
                        f"Setting '{setting_path}' matches default and is not present in user TOML. No change needed."
                    )
                    modified = False # No actual change to the file needed
            else:
                # Setting to a non-default value: update or add the key
                target_section[target_key] = new_value
                logger.openhands_logger.info(
                    f"Updated setting '{setting_path}' in user TOML."
                )
                modified = True

            # Write back to file only if modified
            if modified:
                try:
                    with open(USER_CONFIG_PATH, 'w', encoding='utf-8') as f:
                        tomlkit.dump(user_toml_doc, f)
                    logger.openhands_logger.info(
                        f"Successfully saved user TOML: {USER_CONFIG_PATH}"
                    )
                    # TODO: Update the runtime app_config instance with the new_value
                    #       so the change takes effect immediately without restart.
                    #       This needs careful handling, potentially involving callbacks
                    #       or direct access to the global config object.
                    return True
                except Exception as e:
                    logger.openhands_logger.error(
                        f"Failed to write user TOML file {USER_CONFIG_PATH}: {e}\n{traceback.format_exc()}"
                    )
                    return False
            else:
                return True # Indicate success even if no file write was needed (e.g., removing a non-existent key)

        except (AttributeError, KeyError, TypeError, NotImplementedError) as e:
            logger.openhands_logger.error(
                f"Failed to navigate or update setting '{setting_path}' in user TOML: {e}"
            )
            return False
        except Exception as e:
            logger.openhands_logger.error(
                f"An unexpected error occurred during saving setting '{setting_path}': {e}\n{traceback.format_exc()}"
            )
            return False

    except (AttributeError, KeyError, TypeError, NotImplementedError) as e:
        logger.openhands_logger.error(
            f"Failed to retrieve values for setting path '{setting_path}': {e}"
        )
        return False
    except Exception as e:
        logger.openhands_logger.error(
            f"An unexpected error occurred processing setting '{setting_path}': {e}\n{traceback.format_exc()}"
        )
        return False
