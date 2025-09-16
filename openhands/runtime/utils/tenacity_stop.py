from openhands.utils.shutdown_listener import should_exit
from tenacity import RetryCallState
from tenacity.stop import stop_base


class stop_if_should_exit(stop_base):
    """Stop if the should_exit flag is set."""

    def __call__(self, retry_state: 'RetryCallState') -> bool:
        return should_exit()
