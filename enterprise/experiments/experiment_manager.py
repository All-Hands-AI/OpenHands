from experiments.constants import (
    ENABLE_EXPERIMENT_MANAGER,
)
from experiments.experiment_versions import (
    handle_claude4_vs_gpt5_experiment,
    handle_condenser_max_step_experiment,
    handle_system_prompt_experiment,
)

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.experiments.experiment_manager import ExperimentManager
from openhands.server.session.conversation_init_data import ConversationInitData


class SaaSExperimentManager(ExperimentManager):
    @staticmethod
    def run_conversation_variant_test(
        user_id, conversation_id, conversation_settings
    ) -> ConversationInitData:
        """
        Run conversation variant test and potentially modify the conversation settings
        based on the PostHog feature flags.

        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            conversation_settings: The conversation settings that may include convo_id and llm_model

        Returns:
            The modified conversation settings
        """
        logger.debug(
            'experiment_manager:run_conversation_variant_test:started',
            extra={'user_id': user_id},
        )

        # Skip all experiment processing if the experiment manager is disabled
        if not ENABLE_EXPERIMENT_MANAGER:
            logger.info(
                'experiment_manager:run_conversation_variant_test:skipped',
                extra={'reason': 'experiment_manager_disabled'},
            )
            return conversation_settings

        # Apply conversation-scoped experiments
        conversation_settings = handle_claude4_vs_gpt5_experiment(
            user_id, conversation_id, conversation_settings
        )
        conversation_settings = handle_condenser_max_step_experiment(
            user_id, conversation_id, conversation_settings
        )

        return conversation_settings

    @staticmethod
    def run_config_variant_test(
        user_id: str | None, conversation_id: str, config: OpenHandsConfig
    ) -> OpenHandsConfig:
        """
        Run agent config variant test and potentially modify the OpenHands config
        based on the current experiment type and PostHog feature flags.

        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            config: The OpenHands configuration

        Returns:
            The modified OpenHands configuration
        """
        logger.info(
            'experiment_manager:run_config_variant_test:started',
            extra={'user_id': user_id},
        )

        # Skip all experiment processing if the experiment manager is disabled
        if not ENABLE_EXPERIMENT_MANAGER:
            logger.info(
                'experiment_manager:run_config_variant_test:skipped',
                extra={'reason': 'experiment_manager_disabled'},
            )
            return config

        # Pass the entire OpenHands config to the system prompt experiment
        # Let the experiment handler directly modify the config as needed
        modified_config = handle_system_prompt_experiment(
            user_id, conversation_id, config
        )

        # Condenser max step experiment is applied via conversation variant test,
        # not config variant test. Return modified config from system prompt only.
        return modified_config
