from openhands.events.stream import EventStreamABC


class AgentSdkEventStream(EventStreamABC):
    """
    Interface providing forward compatibility between the old EventStream and the new AgentSDK Conversation API.

    The new AgentSDK offers a list like object in it's state including events - As of 2025-09-10 Xingyao and
    Calvin are working on making this potentially backed by the file system to reduce memory load.
    """

    def search_events(
        self, start_id=0, end_id=None, reverse=False, filter=None, limit=None
    ):
        raise NotImplementedError

    def get_event(self, id):
        raise NotImplementedError

    def get_latest_event(self):
        raise NotImplementedError

    def get_latest_event_id(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def subscribe(self, subscriber_id, callback, callback_id):
        raise NotImplementedError

    def unsubscribe(self, subscriber_id, callback_id):
        raise NotImplementedError

    def add_event(self, event, source):
        raise NotImplementedError

    def set_secrets(self, secrets):
        raise NotImplementedError

    def update_secrets(self, secrets):
        raise NotImplementedError

    def add_task_list(self, task_list: str) -> None:
        raise NotImplementedError

    def read_task_list(self) -> str:
        raise NotImplementedError

    def load_state(self):
        raise NotImplementedError

    def save_state(self, state):
        raise NotImplementedError
