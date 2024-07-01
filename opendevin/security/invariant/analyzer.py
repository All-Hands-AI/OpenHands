import uuid
from dataclasses import asdict
from typing import Optional

import docker

from opendevin.core.const.guide_url import TROUBLESHOOTING_URL
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.action import Action, ActionSecurityRisk
from opendevin.events.event import Event
from opendevin.events.observation import Observation
from opendevin.events.stream import EventStream
from opendevin.runtime.utils import find_available_tcp_port
from opendevin.security.analyzer import SecurityAnalyzer

# from invariant import Monitor
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

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        logger.info('Calling security_risk on InvariantAnalyzer')
        new_elements = parse_element(self.trace, event)
        self.trace.extend(new_elements)
        # input = [asdict(e) for e in self.trace]
        # self.input.extend([asdict(e) for e in new_elements])  # type: ignore [call-overload]
        input = [asdict(e) for e in new_elements]  # type: ignore [call-overload]
        logger.info(f'before policy: {input}')
        errors = self.monitor.check(input)
        logger.info('policy result:')
        logger.info('errors: ' + str(errors))
        if len(errors) > 0:
            return ActionSecurityRisk.MEDIUM
        else:
            return ActionSecurityRisk.LOW
