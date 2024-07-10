import uuid
from dataclasses import asdict
from typing import Optional, List

import docker
import re

from opendevin.core.const.guide_url import TROUBLESHOOTING_URL
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.action import (
    Action,
    ActionSecurityRisk,
)
from opendevin.events.event import Event, EventSource
from opendevin.events.observation import Observation
from opendevin.events.serialization.action import action_from_dict
from opendevin.events.stream import EventStream
from opendevin.runtime.utils import find_available_tcp_port
from opendevin.security.analyzer import SecurityAnalyzer
from opendevin.security.invariant.client import InvariantClient
from opendevin.security.invariant.parser import TraceElement, parse_element
from opendevin.security.invariant.policies import DEFAULT_INVARIANT_POLICY


class InvariantAnalyzer(SecurityAnalyzer):
    """Security analyzer based on Invariant."""

    trace: list[TraceElement]
    input: list[dict]
    container_name: str = 'opendevin-invariant-server'
    image_name: str = 'invariant-server'
    api_host: str = 'http://localhost'
    timeout: int = 120
    settings: dict = {}

    def __init__(
        self,
        event_stream: EventStream,
        policy: Optional[str] = None,
        sid: Optional[str] = None,
    ):
        """Initializes a new instance of the InvariantAnalzyer class."""
        super().__init__(event_stream)
        self.trace = []
        self.input = []
        self.settings = {}
        if policy is None:
            policy = DEFAULT_INVARIANT_POLICY
        if sid is None:
            self.sid = str(uuid.uuid4())

        try:
            self.docker_client = docker.from_env()
        except Exception as ex:
            logger.exception(
                f'Error creating controller. Please check Docker is running and visit `{TROUBLESHOOTING_URL}` for more debugging information.',
                exc_info=False,
            )
            raise ex
        running_containers = self.docker_client.containers.list(
            filters={'name': self.container_name}
        )
        if not running_containers:
            all_containers = self.docker_client.containers.list(
                all=True, filters={'name': self.container_name}
            )
            if all_containers:
                self.container = all_containers[0]
                all_containers[0].start()
            else:
                self.api_port = find_available_tcp_port()
                self.container = self.docker_client.containers.run(
                    self.image_name,
                    name=self.container_name,
                    ports={'8000/tcp': self.api_port},
                    detach=True,
                )
        else:
            self.container = running_containers[0]

        elapsed = 0
        while self.container.status != 'running':
            self.container = self.docker_client.containers.get(self.container_name)
            elapsed += 1
            logger.info(
                f'waiting for container to start: {elapsed}, container status: {self.container.status}'
            )
            if elapsed > self.timeout:
                break

        self.api_port = int(
            self.container.attrs['NetworkSettings']['Ports']['8000/tcp'][0]['HostPort']
        )

        self.api_server = f'{self.api_host}:{self.api_port}'
        self.client = InvariantClient(self.api_server, self.sid)
        self.monitor = self.client.Monitor.from_string(policy)

    def close(self):
        self.container.stop()

    def print_trace(self):
        logger.info('-> Invariant trace:')
        for element in self.trace:
            logger.info('\t-> ' + str(element))

    async def log_event(self, event: Event) -> None:
        if isinstance(event, Observation):
            element = parse_element(self.trace, event)
            self.trace.extend(element)
            self.input.extend([asdict(e) for e in element])  # type: ignore [call-overload]
        else:
            logger.info('Invariant skipping element: event')
        self.print_trace()

    def get_risk(self, results: List[str]) -> ActionSecurityRisk:
        mapping = {"high": ActionSecurityRisk.HIGH, "medium": ActionSecurityRisk.MEDIUM, "low": ActionSecurityRisk.LOW}
        regex = r'(?<=risk=)\w+'
        risks = []
        for result in results:
            m = re.search(regex, result)
            if m and m.group() in mapping:
                risks.append(mapping[m.group()])

        if risks:
            return max(risks)

        return ActionSecurityRisk.LOW

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        logger.info('Calling security_risk on InvariantAnalyzer')
        new_elements = parse_element(self.trace, event)
        input = [asdict(e) for e in new_elements]  # type: ignore [call-overload]
        self.trace.extend(new_elements)
        self.input.extend(input)
        logger.info(f'before policy: {input}')
        result, err = self.monitor.check(input)
        risk = ActionSecurityRisk.UNKNOWN
        if err:
            logger.warning(f'Error checking policy: {err}')
            return risk

        risk = self.get_risk(result)

        # auto-confirm issues based on severity and user setting
        if risk < self.settings.get('RISK_SEVERITY', ActionSecurityRisk.MEDIUM) and hasattr(event, 'is_confirmed') and event.is_confirmed == "awaiting_confirmation":
            logger.info(f'Should handle this event automatically {event}')
            new_event = action_from_dict({"action":"change_agent_state", "args":{"agent_state":"action_confirmed"}})
            if event.source:
                await self.event_stream.add_event(new_event, event.source)
            else:
                await self.event_stream.add_event(new_event, EventSource.AGENT)

        return risk