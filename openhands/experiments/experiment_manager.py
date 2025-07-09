import os

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


# Default to the base ExperimentManager unless overridden by environment variable
experiment_manager_cls = os.environ.get(
    'OPENHANDS_EXPERIMENT_MANAGER_CLS',
    'openhands.experiments.experiment_manager.ExperimentManager',
)
ExperimentManagerImpl = get_impl(ExperimentManager, experiment_manager_cls)
