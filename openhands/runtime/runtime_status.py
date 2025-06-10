from enum import Enum


class RuntimeStatus(Enum):
    def __init__(self, value: str, message: str):
        self._value_ = value
        self.message = message

    STOPPED = 'STATUS$STOPPED', 'Stopped'
    STARTING_RUNTIME = 'STATUS$STARTING_RUNTIME', 'Starting runtime...'
    STARTING_CONTAINER = 'STATUS$STARTING_CONTAINER', 'Starting container...'
    PREPARING_CONTAINER = 'STATUS$PREPARING_CONTAINER', 'Preparing container...'
    CONTAINER_STARTED = 'STATUS$CONTAINER_STARTED', 'Container started.'
    WAITING_FOR_CLIENT = 'STATUS$WAITING_FOR_CLIENT', 'Waiting for client...'
    SETTING_UP_WORKSPACE = 'STATUS$SETTING_UP_WORKSPACE', 'Setting up workspace...'
    SETTING_UP_GIT_HOOKS = 'STATUS$SETTING_UP_GIT_HOOKS', 'Setting up git hooks...'
    READY = 'STATUS$READY', 'Ready...'
