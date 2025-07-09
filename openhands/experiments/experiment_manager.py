import os
from typing import TYPE_CHECKING

from openhands.core.config.agent_config import AgentConfig
from openhands.utils.import_utils import get_impl

if TYPE_CHECKING:
    from openhands.server.session.conversation_init_data import ConversationInitData


class ExperimentManager:
    """
    Base experiment manager class.

    This class provides the interface for experiment managers in OpenHands.
    Subclasses can implement custom experiment logic by overriding the
    run_conversation_variant_test and run_agent_config_variant_test methods.
    """

    @staticmethod
    def run_conversation_variant_test(
        user_id: str, conversation_id: str, conversation_settings: 'ConversationInitData'
    ) -> 'ConversationInitData':
        """
        Apply experiment variations to the conversation settings.

        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            conversation_settings: The original conversation settings

        Returns:
            Modified conversation settings with experiment variations applied
        """
        return conversation_settings

    @staticmethod
    def run_agent_config_variant_test(
        user_id: str, conversation_id: str, agent_config: AgentConfig
    ) -> AgentConfig:
        """
        Apply experiment variations to the agent configuration.

        This method allows experiment managers to modify agent configurations,
        including system prompts, before the agent is created.

        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            agent_config: The original agent configuration

        Returns:
            Modified agent configuration with experiment variations applied
        """
        return agent_config


class AgentExperimentManager(ExperimentManager):
    """
    Experiment manager for agent-related experiments, allowing for system prompt customization.

    This implementation allows for:
    1. Setting a custom system prompt filename via environment variable
    2. Running A/B tests on different system prompts
    """

    @staticmethod
    def run_agent_config_variant_test(
        user_id: str, conversation_id: str, agent_config: AgentConfig
    ) -> AgentConfig:
        """
        Apply experiment variations to the agent configuration.

        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            agent_config: The original agent configuration

        Returns:
            Modified agent configuration with experiment variations applied
        """
        # Create a copy of the config to avoid modifying the original
        modified_config = agent_config.model_copy()

        # Check for custom system prompt filename in environment variables
        custom_system_prompt = os.environ.get('OPENHANDS_SYSTEM_PROMPT_FILENAME')
        if custom_system_prompt:
            # Set the custom system prompt filename
            modified_config.system_prompt_filename = custom_system_prompt

        return modified_config


# Default to the AgentExperimentManager unless overridden by environment variable
experiment_manager_cls = os.environ.get(
    'OPENHANDS_EXPERIMENT_MANAGER_CLS',
    'openhands.experiments.experiment_manager.AgentExperimentManager',
)
ExperimentManagerImpl = get_impl(ExperimentManager, experiment_manager_cls)
