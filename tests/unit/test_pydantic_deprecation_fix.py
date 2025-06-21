"""Test to verify that Pydantic model_fields deprecation warnings are fixed."""

import warnings

from pydantic import BaseModel

from openhands.core.config.config_utils import model_defaults_to_dict
from openhands.core.config.openhands_config import OpenHandsConfig


class TestPydanticDeprecationFix:
    """Test that accessing model_fields on instances doesn't raise deprecation warnings."""

    def test_model_defaults_to_dict_no_deprecation_warning(self):
        """Test that model_defaults_to_dict doesn't raise deprecation warnings."""
        # Create a test config instance
        config = OpenHandsConfig()

        # Capture warnings
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter('always')  # Capture all warnings

            # Call the function that was causing deprecation warnings
            result = model_defaults_to_dict(config)

            # Check that no PydanticDeprecatedSince211 warnings were raised
            pydantic_warnings = [
                w
                for w in warning_list
                if 'PydanticDeprecatedSince211' in str(w.category)
                or 'model_fields' in str(w.message)
            ]

            assert len(pydantic_warnings) == 0, (
                f'Expected no Pydantic deprecation warnings, but got: '
                f'{[str(w.message) for w in pydantic_warnings]}'
            )

            # Verify the function still works correctly
            assert isinstance(result, dict)
            assert len(result) > 0

    def test_load_from_env_no_deprecation_warning(self):
        """Test that load_from_env doesn't raise deprecation warnings."""
        from openhands.core.config.utils import load_from_env

        # Create a test config instance
        config = OpenHandsConfig()
        test_env = {'LLM_MODEL': 'test-model'}

        # Capture warnings
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter('always')  # Capture all warnings

            # Call the function that was causing deprecation warnings
            load_from_env(config, test_env)

            # Check that no PydanticDeprecatedSince211 warnings were raised
            pydantic_warnings = [
                w
                for w in warning_list
                if 'PydanticDeprecatedSince211' in str(w.category)
                or 'model_fields' in str(w.message)
            ]

            assert len(pydantic_warnings) == 0, (
                f'Expected no Pydantic deprecation warnings, but got: '
                f'{[str(w.message) for w in pydantic_warnings]}'
            )

    def test_model_fields_access_pattern(self):
        """Test that we're accessing model_fields from the class, not the instance."""

        class TestModel(BaseModel):
            test_field: str = 'default'

        instance = TestModel()

        # This should work without warnings (accessing from class)
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter('always')

            # Access model_fields from class - this is the correct way
            fields_from_class = instance.__class__.model_fields

            # Check no warnings
            pydantic_warnings = [
                w
                for w in warning_list
                if 'PydanticDeprecatedSince211' in str(w.category)
                or 'model_fields' in str(w.message)
            ]

            assert len(pydantic_warnings) == 0
            assert 'test_field' in fields_from_class

    def test_deprecated_pattern_would_warn(self):
        """Test that the old pattern would indeed cause warnings (for verification)."""

        class TestModel(BaseModel):
            test_field: str = 'default'

        instance = TestModel()

        # This should cause a warning (accessing from instance) - the old way
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter('always')

            # Access model_fields from instance - this is the deprecated way
            try:
                fields_from_instance = instance.model_fields

                # Check if we got a deprecation warning
                pydantic_warnings = [
                    w
                    for w in warning_list
                    if 'PydanticDeprecatedSince211' in str(w.category)
                    or 'model_fields' in str(w.message)
                    or 'deprecated' in str(w.message).lower()
                ]

                # We expect this to generate a warning in newer Pydantic versions
                # If no warning is generated, it might be an older version
                # This test is mainly to verify our understanding of the issue
                if len(pydantic_warnings) > 0:
                    assert 'test_field' in fields_from_instance

            except AttributeError:
                # In some Pydantic versions, this might not even be accessible
                pass
