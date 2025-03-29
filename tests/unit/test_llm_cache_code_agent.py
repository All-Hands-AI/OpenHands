from unittest.mock import MagicMock, patch

import pytest

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.llm_cache_code_agent import LLMCacheCodeAgent
from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.llm import LLM
from openhands.memory.condenser.condenser import Condenser
from openhands.memory.condenser.impl.llm_agent_cache_condenser import LLMAgentCacheCondenser
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


@patch.object(CodeActAgent, '__init__')
def test_llm_cache_code_agent_init(mock_codeact_init):
    """Test that the LLMCacheCodeAgent initializes correctly."""
    # Mock the CodeActAgent.__init__ to avoid calling Condenser.from_config
    mock_codeact_init.return_value = None
    
    # Mock the LLM config
    mock_llm_config = MagicMock()
    mock_llm_config.model = "gpt-4"
    
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True
    mock_llm.config = mock_llm_config
    
    # Mock the agent config with required attributes
    mock_config = MagicMock(spec=AgentConfig)
    mock_config.codeact_enable_browsing = False
    mock_config.codeact_enable_jupyter = False
    mock_config.codeact_enable_llm_editor = False
    
    # Create the agent and set required attributes before __init__ completes
    agent = LLMCacheCodeAgent.__new__(LLMCacheCodeAgent)
    agent.conversation_memory = MagicMock(spec=ConversationMemory)
    agent.prompt_manager = MagicMock(spec=PromptManager)
    
    # Now call __init__ manually
    LLMCacheCodeAgent.__init__(agent, llm=mock_llm, config=mock_config)
    
    # Verify that the agent has a LLMAgentCacheCondenser
    assert isinstance(agent._condenser, LLMAgentCacheCondenser)
    
    # Verify that the condenser uses the same LLM as the agent
    assert agent._condenser.llm is mock_llm
    
    # Verify that the condenser has the agent's conversation_memory and prompt_manager
    assert agent._condenser.conversation_memory is agent.conversation_memory
    assert agent._condenser.prompt_manager is agent.prompt_manager


@patch.object(CodeActAgent, '__init__')
def test_llm_cache_code_agent_init_missing_dependencies(mock_codeact_init):
    """Test that the LLMCacheCodeAgent raises an exception when dependencies are missing."""
    # Mock the CodeActAgent.__init__ to avoid calling Condenser.from_config
    mock_codeact_init.return_value = None
    
    # Mock the LLM config
    mock_llm_config = MagicMock()
    mock_llm_config.model = "gpt-4"
    
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True
    mock_llm.config = mock_llm_config
    
    # Mock the agent config with required attributes
    mock_config = MagicMock(spec=AgentConfig)
    
    # Verify that creating the agent raises an exception
    with pytest.raises(ValueError, match="Missing conversation_memory or prompt_manager"):
        LLMCacheCodeAgent(
            llm=mock_llm,
            config=mock_config,
        )


def test_llm_cache_code_agent_condenser_class():
    """Test that the LLMCacheCodeAgent returns the correct condenser class."""
    assert LLMCacheCodeAgent.get_condenser_class() is LLMAgentCacheCondenser


@patch.object(CodeActAgent, '__init__')
def test_llm_cache_code_agent_condensed_history(mock_codeact_init):
    """Test that the LLMCacheCodeAgent uses its condenser for condensed_history."""
    # Mock the CodeActAgent.__init__ to avoid calling Condenser.from_config
    mock_codeact_init.return_value = None
    
    # Create the agent and set required attributes before __init__ completes
    agent = LLMCacheCodeAgent.__new__(LLMCacheCodeAgent)
    agent.conversation_memory = MagicMock(spec=ConversationMemory)
    agent.prompt_manager = MagicMock(spec=PromptManager)
    
    # Manually set the condenser
    agent._condenser = MagicMock(spec=LLMAgentCacheCondenser)
    
    # Mock the state
    mock_state = MagicMock()
    
    # Call the agent's condensed_history method
    agent.condensed_history(mock_state)
    
    # Verify that the condenser's condensed_history method was called
    agent._condenser.condensed_history.assert_called_once_with(mock_state)


@patch.object(CodeActAgent, '__init__')
@patch('openhands.memory.condenser.impl.llm_agent_cache_condenser.LLMAgentCacheCondenser.__init__')
def test_llm_cache_code_agent_with_condenser_parameters(mock_condenser_init, mock_codeact_init):
    """Test that the LLMCacheCodeAgent passes the correct parameters to the condenser."""
    # Mock the CodeActAgent.__init__ to avoid calling Condenser.from_config
    mock_codeact_init.return_value = None
    
    # Mock the LLMAgentCacheCondenser.__init__ to avoid actual initialization
    mock_condenser_init.return_value = None
    
    # Mock the LLM config
    mock_llm_config = MagicMock()
    mock_llm_config.model = "gpt-4"
    
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True
    mock_llm.config = mock_llm_config
    
    # Mock the agent config with required attributes
    mock_config = MagicMock(spec=AgentConfig)
    
    # Create the agent and set required attributes before __init__ completes
    agent = LLMCacheCodeAgent.__new__(LLMCacheCodeAgent)
    agent.conversation_memory = MagicMock(spec=ConversationMemory)
    agent.prompt_manager = MagicMock(spec=PromptManager)
    
    # Reset the mock to clear any previous calls
    mock_condenser_init.reset_mock()
    
    # Now call __init__ manually
    LLMCacheCodeAgent.__init__(agent, llm=mock_llm, config=mock_config)
    
    # Verify that the condenser was initialized with the correct parameters
    mock_condenser_init.assert_called_once()
    
    # Get the call arguments
    args, kwargs = mock_condenser_init.call_args
    
    # Check that the required parameters were passed
    assert kwargs['agent_llm'] is mock_llm
    assert kwargs['conversation_memory'] is agent.conversation_memory
    assert kwargs['prompt_manager'] is agent.prompt_manager