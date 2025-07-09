import os

from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.utils.import_utils import get_impl


class ExperimentManager:
    """
    Base experiment manager class.

    This class provides the interface for experiment managers in OpenHands.
    Subclasses can implement custom experiment logic by overriding the
    run_conversation_variant_test method.
    """

    @staticmethod
    def run_conversation_variant_test(
        user_id: str, conversation_id: str, conversation_settings: ConversationInitData
    ) -> ConversationInitData:
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


class AgentExperimentManager(ExperimentManager):
    """
    Experiment manager for agent-related experiments, allowing for system prompt customization.

    This implementation allows for:
    1. Setting a custom system prompt filename via environment variable
    2. Running A/B tests on different system prompts
    """

    @staticmethod
    def run_conversation_variant_test(
        user_id: str, conversation_id: str, conversation_settings: ConversationInitData
    ) -> ConversationInitData:
        """
        Apply experiment variations to the conversation settings.

        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            conversation_settings: The original conversation settings

        Returns:
            Modified conversation settings with experiment variations applied
        """
        # Create a copy of the settings to avoid modifying the original
        modified_settings = conversation_settings.model_copy()

        # Check for custom system prompt filename in environment variables
        custom_system_prompt = os.environ.get('OPENHANDS_SYSTEM_PROMPT_FILENAME')
        if custom_system_prompt:
            logger.info(
                f'Using custom system prompt from environment: {custom_system_prompt}',
                extra={
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'experiment': 'custom_system_prompt',
                },
            )

            # If agent_config doesn't exist, create it
            if not modified_settings.agent_config:
                modified_settings.agent_config = AgentConfig()

            # Set the custom system prompt filename
            modified_settings.agent_config.system_prompt_filename = custom_system_prompt

        # Example of A/B testing based on conversation_id (can be expanded as needed)
        # This is just a placeholder for future A/B testing implementation
        # if conversation_id and int(conversation_id[:8], 16) % 2 == 0:
        #     logger.info(
        #         f"Assigning conversation {conversation_id} to experiment group A",
        #         extra={
        #             'user_id': user_id,
        #             'conversation_id': conversation_id,
        #             'experiment': 'system_prompt_ab_test',
        #             'group': 'A',
        #         },
        #     )
        #     # Apply group A settings
        #     if not modified_settings.agent_config:
        #         modified_settings.agent_config = AgentConfig()
        #     modified_settings.agent_config.system_prompt_filename = 'system_prompt_a.j2'
        # else:
        #     logger.info(
        #         f"Assigning conversation {conversation_id} to experiment group B",
        #         extra={
        #             'user_id': user_id,
        #             'conversation_id': conversation_id,
        #             'experiment': 'system_prompt_ab_test',
        #             'group': 'B',
        #         },
        #     )
        #     # Apply group B settings
        #     if not modified_settings.agent_config:
        #         modified_settings.agent_config = AgentConfig()
        #     modified_settings.agent_config.system_prompt_filename = 'system_prompt_b.j2'

        return modified_settings


# Default to the AgentExperimentManager unless overridden by environment variable
experiment_manager_cls = os.environ.get(
    'OPENHANDS_EXPERIMENT_MANAGER_CLS',
    'openhands.experiments.experiment_manager.AgentExperimentManager',
)
ExperimentManagerImpl = get_impl(ExperimentManager, experiment_manager_cls)
