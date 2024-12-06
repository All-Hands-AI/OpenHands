from enum import Enum


class ReplayDebuggingPhase(str, Enum):
    Normal = 'normal'
    """The agent is not doing anything related to Replay.
    """
    Analysis = 'analysis'
    """The agent is analyzing a recording.
    """
    Edit = 'edit'
    """The agent is editing the code.
    """
