"""
Example experiment manager that demonstrates how to customize system prompts.

This example shows how to create a custom experiment manager that modifies
the agent's system prompt based on environment variables or other criteria.

To use this experiment manager:
1. Set the environment variable:
   export OPENHANDS_EXPERIMENT_MANAGER_CLS=examples.custom_system_prompt_experiment.CustomSystemPromptExperiment

2. Optionally set a custom system prompt filename:
   export OPENHANDS_SYSTEM_PROMPT_FILENAME=my_custom_prompt.j2

3. Run OpenHands as usual
"""

import os

from openhands.core.config.agent_config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.experiments.experiment_manager import ExperimentManager


class CustomSystemPromptExperiment(ExperimentManager):
    """
    Example experiment manager that customizes system prompts.
    
    This implementation demonstrates:
    1. Setting a custom system prompt filename via environment variable
    2. Logging experiment activities for analysis
    3. Preserving the original config while making modifications
    """

    @staticmethod
    def run_agent_config_variant_test(
        user_id: str, conversation_id: str, agent_config: AgentConfig
    ) -> AgentConfig:
        """
        Apply custom system prompt modifications to the agent configuration.

        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            agent_config: The original agent configuration

        Returns:
            Modified agent configuration with custom system prompt
        """
        # Create a copy of the config to avoid modifying the original
        modified_config = agent_config.model_copy()

        # Check for custom system prompt filename in environment variables
        custom_system_prompt = os.environ.get('OPENHANDS_SYSTEM_PROMPT_FILENAME')
        if custom_system_prompt:
            logger.info(
                f'Using custom system prompt from environment: {custom_system_prompt}',
                extra={
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'experiment': 'custom_system_prompt',
                    'original_prompt': modified_config.system_prompt_filename,
                    'custom_prompt': custom_system_prompt,
                },
            )

            # Set the custom system prompt filename
            modified_config.system_prompt_filename = custom_system_prompt
        else:
            logger.info(
                'No custom system prompt specified, using default',
                extra={
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'experiment': 'custom_system_prompt',
                    'prompt': modified_config.system_prompt_filename,
                },
            )

        return modified_config