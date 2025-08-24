from enum import Enum

# TODO: I think this class should be deprecated and replaced with `RuntimeStatus` - the values for which are
# defined in the runtime api:
# * running: currently RUNNING
# * stopped currently ARCHIVED
# * paused: currently STOPPED
# * error: currently ERROR
# * starting: currently STARTING
#
# Unifying these two would simplify the codebase - particularly related to what `STOPPED` actually means.
# Calling this `RuntimeStatus` is more descriptive of what this actually means too.


class ConversationStatus(Enum):
    # The runtime is starting
    STARTING = 'STARTING'
    # The conversation is running - the agent may be working or idle
    RUNNING = 'RUNNING'
    # The conversation has stopped (This is synonymous with `paused` in the runtime API.)
    STOPPED = 'STOPPED'
    # The conversation has been archived and cannot be restarted.
    ARCHIVED = 'ARCHIVED'
    # Something has gone wrong with the conversation
    ERROR = 'ERROR'
