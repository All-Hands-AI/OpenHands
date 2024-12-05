from enum import Enum


class ReplayAnalysisPhase(str, Enum):
    Normal = 'normal'
    """The agent is not doing anything related to Replay.
    """
    Analyzing = 'analyzing'
    """The agent is analyzing a recording.
    """
