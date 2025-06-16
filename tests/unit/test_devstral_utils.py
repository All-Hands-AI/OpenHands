"""Tests for Devstral utilities."""

from openhands.llm.devstral_utils import (
    DEVSTRAL_SYSTEM_PROMPT,
    ensure_devstral_system_prompt,
    inject_devstral_system_prompt,
    is_devstral_model,
    is_ollama_provider,
    needs_devstral_system_prompt_injection,
)


class TestDevstralUtils:
    """Test Devstral utility functions."""

    def test_is_devstral_model(self):
        """Test detection of Devstral models."""
        assert is_devstral_model('mistralai/devstral-small-2505')
        assert is_devstral_model('devstral')
        assert is_devstral_model('DEVSTRAL-LARGE')
        assert not is_devstral_model('mistralai/mistral-7b')
        assert not is_devstral_model('gpt-4')
        assert not is_devstral_model('claude-3')

    def test_is_ollama_provider(self):
        """Test detection of Ollama provider."""
        # Test via custom_llm_provider
        assert is_ollama_provider(None, 'ollama')
        assert is_ollama_provider(None, 'OLLAMA')
        assert not is_ollama_provider(None, 'openai')

        # Test via base_url
        assert is_ollama_provider('http://localhost:11434', None)
        assert is_ollama_provider('https://ollama.example.com', None)
        assert not is_ollama_provider('https://api.openai.com', None)

        # Test both None
        assert not is_ollama_provider(None, None)

    def test_needs_devstral_system_prompt_injection(self):
        """Test logic for determining when to inject system prompt."""
        # Should inject for Devstral + Ollama without system message
        messages = [{'role': 'user', 'content': 'Hello'}]
        assert needs_devstral_system_prompt_injection(
            'devstral', 'http://localhost:11434', None, messages
        )

        # Should not inject for non-Devstral models
        assert not needs_devstral_system_prompt_injection(
            'gpt-4', 'http://localhost:11434', None, messages
        )

        # Should not inject for non-Ollama providers
        assert not needs_devstral_system_prompt_injection(
            'devstral', 'https://api.openai.com', None, messages
        )

        # Should not inject if Devstral system message already exists
        messages_with_devstral = [
            {
                'role': 'system',
                'content': 'You are Devstral, a helpful agentic model...',
            },
            {'role': 'user', 'content': 'Hello'},
        ]
        assert not needs_devstral_system_prompt_injection(
            'devstral', 'http://localhost:11434', None, messages_with_devstral
        )

    def test_inject_devstral_system_prompt_no_existing_system(self):
        """Test injecting system prompt when no system message exists."""
        messages = [{'role': 'user', 'content': 'Hello'}]
        result = inject_devstral_system_prompt(messages)

        assert len(result) == 2
        assert result[0]['role'] == 'system'
        assert result[0]['content'] == DEVSTRAL_SYSTEM_PROMPT
        assert result[1]['role'] == 'user'
        assert result[1]['content'] == 'Hello'

    def test_inject_devstral_system_prompt_replace_existing_system(self):
        """Test replacing existing system message with Devstral prompt."""
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant'},
            {'role': 'user', 'content': 'Hello'},
        ]
        result = inject_devstral_system_prompt(messages)

        assert len(result) == 2
        assert result[0]['role'] == 'system'
        assert result[0]['content'] == DEVSTRAL_SYSTEM_PROMPT
        assert result[1]['role'] == 'user'
        assert result[1]['content'] == 'Hello'

    def test_ensure_devstral_system_prompt_injection_needed(self):
        """Test the main function when injection is needed."""
        messages = [{'role': 'user', 'content': 'Hello'}]
        result = ensure_devstral_system_prompt(
            'devstral', 'http://localhost:11434', None, messages
        )

        assert len(result) == 2
        assert result[0]['role'] == 'system'
        assert result[0]['content'] == DEVSTRAL_SYSTEM_PROMPT

    def test_ensure_devstral_system_prompt_injection_not_needed(self):
        """Test the main function when injection is not needed."""
        messages = [{'role': 'user', 'content': 'Hello'}]
        result = ensure_devstral_system_prompt(
            'gpt-4', 'https://api.openai.com', None, messages
        )

        # Should return original messages unchanged
        assert result == messages
        assert len(result) == 1
        assert result[0]['role'] == 'user'

    def test_devstral_system_prompt_content(self):
        """Test that the Devstral system prompt contains expected content."""
        assert 'Devstral' in DEVSTRAL_SYSTEM_PROMPT
        assert 'OpenHands scaffold' in DEVSTRAL_SYSTEM_PROMPT
        assert '<ROLE>' in DEVSTRAL_SYSTEM_PROMPT
        assert '<EFFICIENCY>' in DEVSTRAL_SYSTEM_PROMPT
        assert '<FILE_SYSTEM_GUIDELINES>' in DEVSTRAL_SYSTEM_PROMPT
