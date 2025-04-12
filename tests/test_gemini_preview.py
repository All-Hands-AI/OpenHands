import unittest
from unittest.mock import patch

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM


class TestGeminiPreview(unittest.TestCase):
    @patch('litellm.supports_function_calling')
    def test_gemini_preview_function_calling(self, mock_supports_function_calling):
        # Mock litellm.supports_function_calling to return True
        mock_supports_function_calling.return_value = True

        # Test with regular gemini-2.5-pro model
        config = LLMConfig(model="gemini/gemini-2.5-pro")
        llm = LLM(config)
        self.assertTrue(llm.is_function_calling_active())

        # Test with preview version
        config = LLMConfig(model="gemini/gemini-2.5-pro-preview-03-25")
        llm = LLM(config)
        self.assertTrue(llm.is_function_calling_active())

        # Test with another preview version
        config = LLMConfig(model="gemini-2.5-pro-preview-04-01")
        llm = LLM(config)
        self.assertTrue(llm.is_function_calling_active())

        # Test with a non-supported model
        config = LLMConfig(model="gemini/gemini-1.0-not-supported")
        llm = LLM(config)
        # This should be False since it's not in FUNCTION_CALLING_SUPPORTED_MODELS
        # and doesn't match the pattern
        self.assertFalse(llm.is_function_calling_active())


if __name__ == "__main__":
    unittest.main()