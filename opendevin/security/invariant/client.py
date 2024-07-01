import time
from typing import Optional

import requests
from requests.exceptions import ConnectionError


class InvariantClient:
    timeout: int = 120

    def __init__(self, server_url: str, session_id: Optional[str] = None):
        self.server = server_url
        self.session_id = self._create_session()
        self.Policy = self._Policy(self)
        self.Monitor = self._Monitor(self)

    def _create_session(self, session_id: Optional[str] = None):
        elapsed = 0
        while elapsed < self.timeout:
            try:
                if session_id:
                    response = requests.get(
                        f'{self.server}/session/new?session_id={session_id}'
                    )
                else:
                    response = requests.get(f'{self.server}/session/new')
                break
            except ConnectionError:
                elapsed += 1
                time.sleep(1)
        return response.json()['id']

    def close_session(self):
        requests.delete(f'{self.server}/session/?session_id={self.session_id}')

    class _Policy:
        def __init__(self, invariant):
            self.server = invariant.server
            self.session_id = invariant.session_id

        def _create_policy(self, rule):
            response = requests.post(
                f'{self.server}/policy/new?session_id={self.session_id}',
                json={'rule': rule},
            )
            return response.json()['policy_id']

        def from_string(self, rule):
            self.policy_id = self._create_policy(rule)
            return self

        def analyze(self, trace):
            response = requests.post(
                f'{self.server}/policy/{self.policy_id}/analyze?session_id={self.session_id}',
                json={'trace': trace},
            )
            return response.json()

    class _Monitor:
        def __init__(self, invariant):
            self.server = invariant.server
            self.session_id = invariant.session_id

        def _create_monitor(self, rule):
            response = requests.post(
                f'{self.server}/monitor/new?session_id={self.session_id}',
                json={'rule': rule},
            )
            return response.json()['monitor_id']

        def from_string(self, rule):
            self.monitor_id = self._create_monitor(rule)
            return self

        def check(self, trace):
            response = requests.post(
                f'{self.server}/monitor/{self.monitor_id}/check?session_id={self.session_id}',
                json={'trace': trace},
            )
            return response.text
