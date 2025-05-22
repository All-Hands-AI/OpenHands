import pytest

from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.app_config import AppConfig
from openhands.core.config.utils import finalize_config, load_from_env, load_from_toml

# Define a dummy agent name often used in tests or as a default
DEFAULT_AGENT_NAME = 'CodeActAgent'

def test_finalize_config_cli_disables_jupyter_when_true():
    """
    Test that finalize_config sets enable_jupyter to False for an agent
    when runtime is 'cli' and enable_jupyter was initially True.
    """
    app_config = AppConfig()
    app_config.runtime = 'cli'
    
    # Create a specific agent config
    agent_config = AgentConfig(enable_jupyter=True)
    app_config.agents[DEFAULT_AGENT_NAME] = agent_config
    
    finalize_config(app_config)
    
    assert not app_config.agents[DEFAULT_AGENT_NAME].enable_jupyter, \
        "enable_jupyter should be False when runtime is 'cli'"

def test_finalize_config_cli_keeps_jupyter_false_when_false():
    """
    Test that finalize_config keeps enable_jupyter as False for an agent
    when runtime is 'cli' and enable_jupyter was initially False.
    """
    app_config = AppConfig()
    app_config.runtime = 'cli'
    
    agent_config = AgentConfig(enable_jupyter=False)
    app_config.agents[DEFAULT_AGENT_NAME] = agent_config
    
    finalize_config(app_config)
    
    assert not app_config.agents[DEFAULT_AGENT_NAME].enable_jupyter, \
        "enable_jupyter should remain False when runtime is 'cli' and initially False"

def test_finalize_config_other_runtime_keeps_jupyter_true_by_default():
    """
    Test that finalize_config keeps enable_jupyter as True (default) for an agent
    when runtime is not 'cli'.
    """
    app_config = AppConfig()
    app_config.runtime = 'docker'  # A non-cli runtime
    
    # AgentConfig defaults enable_jupyter to True
    agent_config = AgentConfig() 
    app_config.agents[DEFAULT_AGENT_NAME] = agent_config
    
    finalize_config(app_config)
    
    assert app_config.agents[DEFAULT_AGENT_NAME].enable_jupyter, \
        "enable_jupyter should remain True by default for non-cli runtimes"

def test_finalize_config_other_runtime_keeps_jupyter_false_if_set():
    """
    Test that finalize_config keeps enable_jupyter as False for an agent
    when runtime is not 'cli' but it was explicitly set to False.
    """
    app_config = AppConfig()
    app_config.runtime = 'docker'  # A non-cli runtime
    
    agent_config = AgentConfig(enable_jupyter=False)
    app_config.agents[DEFAULT_AGENT_NAME] = agent_config
    
    finalize_config(app_config)
    
    assert not app_config.agents[DEFAULT_AGENT_NAME].enable_jupyter, \
        "enable_jupyter should remain False for non-cli runtimes if explicitly set to False"

def test_finalize_config_no_agents_defined():
    """
    Test that finalize_config runs without error if no agents are defined in the config,
    even when runtime is 'cli'.
    """
    app_config = AppConfig()
    app_config.runtime = 'cli'
    # No agents are added to app_config.agents
    
    try:
        finalize_config(app_config)
    except Exception as e:
        pytest.fail(f"finalize_config raised an exception with no agents defined: {e}")

def test_finalize_config_multiple_agents_cli_runtime():
    """
    Test that finalize_config correctly disables jupyter for multiple agents
    when runtime is 'cli'.
    """
    app_config = AppConfig()
    app_config.runtime = 'cli'
    
    agent_config1 = AgentConfig(enable_jupyter=True)
    agent_config2 = AgentConfig(enable_jupyter=True)
    app_config.agents['Agent1'] = agent_config1
    app_config.agents['Agent2'] = agent_config2
    
    finalize_config(app_config)
    
    assert not app_config.agents['Agent1'].enable_jupyter, "Jupyter should be disabled for Agent1"
    assert not app_config.agents['Agent2'].enable_jupyter, "Jupyter should be disabled for Agent2"

def test_finalize_config_multiple_agents_other_runtime():
    """
    Test that finalize_config correctly keeps jupyter enabled (or as set) for multiple agents
    when runtime is not 'cli'.
    """
    app_config = AppConfig()
    app_config.runtime = 'docker'
    
    agent_config1 = AgentConfig(enable_jupyter=True) # Default
    agent_config2 = AgentConfig(enable_jupyter=False) # Explicitly false
    app_config.agents['Agent1'] = agent_config1
    app_config.agents['Agent2'] = agent_config2
    
    finalize_config(app_config)
    
    assert app_config.agents['Agent1'].enable_jupyter, "Jupyter should be True for Agent1"
    assert not app_config.agents['Agent2'].enable_jupyter, "Jupyter should be False for Agent2"