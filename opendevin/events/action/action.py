from opendevin.events import Event

class Action(Event):
    action: str

    async def run(self, controller: 'AgentController') -> 'Observation':
        raise NotImplementedError

    def to_memory(self):
        d = super().to_memory()
        try:
            v = d.pop('action')
        except KeyError:
            raise NotImplementedError(f'{self=} does not have action attribute set')
        return {'action': v, 'args': d}

    @property
    def executable(self) -> bool:
        raise NotImplementedError

