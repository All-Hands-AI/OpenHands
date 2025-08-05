from unittest.mock import Mock, patch

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.message import Message, TextContent
from openhands.events.action.agent import KnowledgeBaseAction
from openhands.llm.llm import LLM


class TestKnowledgeAction:
    """Unit tests for KnowledgeBaseAction and knowledge base handling"""

    def test_knowledge_base_action_creation(self):
        """Test basic KnowledgeBaseAction creation"""
        content = 'Test knowledge base content'
        action = KnowledgeBaseAction(content=content, enable_think=False)

        assert action.content == content
        assert action.enable_think is False
        assert action.action == 'knowledge_base'
        assert action.message == content

    def test_knowledge_base_action_string_representation(self):
        """Test string representation of KnowledgeBaseAction"""
        content = 'Test knowledge content'
        action = KnowledgeBaseAction(content=content)

        str_repr = str(action)
        assert 'Knowledgebase Action' in str_repr
        assert content in str_repr

    def test_knowledge_base_not_cached_by_default(self):
        """Test that knowledge base content is NOT cached by default"""
        # Test the knowledge base text content directly
        knowledge_text = 'Test knowledge base content'
        text_content = TextContent(text=knowledge_text)

        # Verify that cache_prompt defaults to False
        assert text_content.cache_prompt is False

        # Test serialization doesn't include cache control
        serialized = text_content.serialize_model()
        assert 'cache_control' not in serialized

    def test_knowledge_base_content_with_caching_enabled(self):
        """Test that knowledge base content can be cached when explicitly enabled"""
        # Create TextContent with caching enabled
        knowledge_text = 'Test knowledge base with caching'
        text_content = TextContent(text=knowledge_text, cache_prompt=True)

        # Verify cache_prompt is set
        assert text_content.cache_prompt is True

        # Test serialization includes cache control
        serialized = text_content.serialize_model()
        assert 'cache_control' in serialized
        assert serialized['cache_control']['type'] == 'ephemeral'

    def test_knowledge_base_content_without_caching(self):
        """Test that knowledge base content without caching doesn't include cache control"""
        knowledge_text = 'Test knowledge base without caching'
        text_content = TextContent(
            text=knowledge_text
        )  # cache_prompt defaults to False

        # Verify cache_prompt is False by default
        assert text_content.cache_prompt is False

        # Test serialization doesn't include cache control
        serialized = text_content.serialize_model()
        assert 'cache_control' not in serialized

    def test_knowledge_base_protocol_content(self):
        """Test that knowledge base protocol contains expected content"""
        # Test _handle_knowledge_base method by creating a minimal agent instance
        llm_config = LLMConfig(model='gpt-4')
        agent_config = AgentConfig()
        llm = Mock(spec=LLM)
        llm.config = llm_config  # Add config to mock

        # Create agent with mocked dependencies
        with patch(
            'openhands.agenthub.codeact_agent.function_calling.get_tools',
            return_value=[],
        ):
            agent = CodeActAgent(llm=llm, config=agent_config)
            agent.space_id = 1  # Enable knowledge base handling

            kb_content = agent._handle_knowledge_base()

            # Check that protocol contains expected elements
            assert 'KNOWLEDGE BASE EVALUATION PROTOCOL' in kb_content
            assert '<KnowledgeBase>' in kb_content
            assert '<XResult>' in kb_content
            assert 'Relevance Assessment' in kb_content
            assert 'Completeness Analysis' in kb_content
            assert 'Strategic Decision' in kb_content

    def test_knowledge_base_disabled_when_no_space_id(self):
        """Test that knowledge base is disabled when space_id is None"""
        llm_config = LLMConfig(model='gpt-4')
        agent_config = AgentConfig()
        llm = Mock(spec=LLM)
        llm.config = llm_config  # Add config to mock

        # Create agent with mocked dependencies
        with patch(
            'openhands.agenthub.codeact_agent.function_calling.get_tools',
            return_value=[],
        ):
            agent = CodeActAgent(llm=llm, config=agent_config)
            # Don't set space_id or thread_follow_up (they default to None)

            kb_content = agent._handle_knowledge_base()

            # Should return empty string when disabled
            assert kb_content == ''

    def test_knowledge_base_appended_to_system_message(self):
        """Test that knowledge base content is appended to system message"""
        knowledge_text = 'Test knowledge base content'

        # Create system message with knowledge base appended
        system_message = Message(
            role='system',
            content=[
                TextContent(text='System prompt'),
                TextContent(text=knowledge_text),  # Knowledge base appended
            ],
        )

        # Verify knowledge base is in system message
        assert len(system_message.content) == 2
        assert system_message.content[1].text == knowledge_text
        assert system_message.content[1].cache_prompt is False  # Not cached by default

    def test_knowledge_base_caching_in_system_message(self):
        """Test that knowledge base can be cached when added to system message"""
        knowledge_text = 'Test knowledge base content with caching'

        # Create system message with cached knowledge base and enable caching
        system_message = Message(
            role='system',
            content=[
                TextContent(text='System prompt'),
                TextContent(
                    text=knowledge_text, cache_prompt=True
                ),  # Cached knowledge base
            ],
            cache_enabled=True,  # Enable list serialization mode for caching
        )

        # Verify caching is enabled
        assert system_message.content[1].cache_prompt is True

        # Test message serialization with caching (list mode)
        serialized = system_message.serialize_model()
        assert 'content' in serialized
        assert isinstance(serialized['content'], list)
        assert len(serialized['content']) == 2
        # The cached content should have cache_control
        assert 'cache_control' in serialized['content'][1]
