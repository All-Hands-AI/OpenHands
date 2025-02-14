from dataclasses import dataclass

from openhands.events.observation.observation import Observation


@dataclass
class SearchSecretsObservation(Observation):
    """This data class represents the output of a search for secret."""
