from enum import Enum


class RuntimeStatus(Enum):
    def __init__(self, value: str, message: str):
        self._value_ = value
        self.message = message

    STOPPED = 'STATUS$STOPPED', 'Stopped'
    BUILDING_RUNTIME = 'STATUS$BUILDING_RUNTIME', 'Building runtime...'
    STARTING_RUNTIME = 'STATUS$STARTING_RUNTIME', 'Starting runtime...'
    RUNTIME_STARTED = 'STATUS$RUNTIME_STARTED', 'Runtime started...'
    SETTING_UP_WORKSPACE = 'STATUS$SETTING_UP_WORKSPACE', 'Setting up workspace...'
    SETTING_UP_GIT_HOOKS = 'STATUS$SETTING_UP_GIT_HOOKS', 'Setting up git hooks...'
    READY = 'STATUS$READY', 'Ready...'
