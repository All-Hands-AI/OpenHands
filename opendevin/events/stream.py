import asyncio
import json
import threading
from datetime import datetime
from enum import Enum
from typing import Callable, Iterable

from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.agent import AgentSummarizeAction
from opendevin.events.observation.summary import SummaryObservation
from opendevin.events.serialization.event import event_from_dict, event_to_dict
from opendevin.storage import FileStore, get_file_store

from .event import Event, EventSource


class EventStreamSubscriber(str, Enum):
    AGENT_CONTROLLER = 'agent_controller'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MAIN = 'main'
    TEST = 'test'


class EventStream:
    sid: str
    _subscribers: dict[str, Callable]
    _cur_id: int
    _lock: threading.Lock
    _file_store: FileStore

    def __init__(self, sid: str):
        self.sid = sid
        self._file_store = get_file_store()
        self._subscribers = {}
        self._cur_id = 0
        self._lock = threading.Lock()
        self._reinitialize_from_file_store()

    def _reinitialize_from_file_store(self):
        try:
            events = self._file_store.list(f'sessions/{self.sid}/events')
        except FileNotFoundError:
            logger.warning(f'No events found for session {self.sid}')
            return
        for event_str in events:
            id = self._get_id_from_filename(event_str)
            if id >= self._cur_id:
                self._cur_id = id + 1

    def _get_filename_for_id(self, id: int) -> str:
        return f'sessions/{self.sid}/events/{id}.json'

    def _get_id_from_filename(self, filename: str) -> int:
        return int(filename.split('/')[-1].split('.')[0])

    def get_events(self, start_id=0, end_id=None) -> Iterable[Event]:
        event_id = start_id
        logger.debug(f'Getting events from {start_id} to {end_id}')
        while True:
            if end_id is not None and event_id > end_id:
                break
            try:
                event = self.get_event(event_id)
                logger.debug(f'{event_id}: {event}')
            except FileNotFoundError:
                break
            yield event
            event_id += 1

    def get_event(self, id: int) -> Event:
        filename = self._get_filename_for_id(id)
        content = self._file_store.read(filename)
        data = json.loads(content)
        return event_from_dict(data)

    def subscribe(self, id: EventStreamSubscriber, callback: Callable):
        if id in self._subscribers:
            raise ValueError('Subscriber already exists: ' + id)
        else:
            self._subscribers[id] = callback

    def unsubscribe(self, id: EventStreamSubscriber):
        if id not in self._subscribers:
            logger.warning('Subscriber not found during unsubscribe: ' + id)
        else:
            del self._subscribers[id]

    def add_event(self, event: Event, source: EventSource):
        with self._lock:
            event._id = self._cur_id  # type: ignore [attr-defined]
            self._cur_id += 1
            event._timestamp = datetime.now()  # type: ignore [attr-defined]
            event._source = source  # type: ignore [attr-defined]
            data = event_to_dict(event)
            if event.id is not None:
                self._file_store.write(
                    self._get_filename_for_id(event.id), json.dumps(data)
                )
            if isinstance(event, AgentSummarizeAction):
                self.replace_events_with_summary(event)
            for key, fn in self._subscribers.items():
                logger.debug(f'Notifying subscriber {key}')
                asyncio.create_task(fn(event))
        logger.debug(f'Done with self._lock for event: {event}')

    def replace_events_with_summary(self, summary_action: AgentSummarizeAction):
        with self._lock:
            start_id = summary_action._chunk_start
            end_id = summary_action._chunk_end

            # get the first event in the chunk
            first_event = self.get_event(start_id)
            first_event_dict = event_to_dict(first_event)

            # create the summary observation
            summary_observation = SummaryObservation(content=summary_action.summary)

            # update the summary action and observation with timestamp and source
            # id, timestamp are those of the first event in the chunk
            summary_action._id = start_id  # type: ignore [attr-defined]
            summary_action._timestamp = first_event_dict['_timestamp']  # type: ignore [attr-defined]
            # AgentSummarizeAction enumerates agent actions
            summary_action._source = EventSource.AGENT  # type: ignore [attr-defined]

            # timestamp is the timestamp of the first event in the chunk
            summary_observation._id = start_id + 1  # type: ignore [attr-defined]
            summary_observation._timestamp = first_event_dict['_timestamp']  # type: ignore [attr-defined]
            # SummaryObservation is set as user, like other observations of the output
            summary_observation._source = EventSource.USER  # type: ignore [attr-defined]
            summary_observation._cause = summary_action.id  # type: ignore [attr-defined]

            # remove the events that were summarized
            for event_id in range(start_id, end_id):
                filename = self._get_filename_for_id(event_id)
                self._file_store.delete(filename)

            # save the summary action and observation to the file store
            summary_action_dict = event_to_dict(summary_action)
            summary_observation_dict = event_to_dict(summary_observation)

            # the filenames will be in order, ids here are first/second event in the replaced chunk
            if summary_action.id is not None and summary_observation.id is not None:
                self._file_store.write(
                    self._get_filename_for_id(summary_action.id),
                    json.dumps(summary_action_dict),
                )
                self._file_store.write(
                    self._get_filename_for_id(summary_observation.id),
                    json.dumps(summary_observation_dict),
                )

            # notify subscribers of the addition of the summary action and observation
            for key, fn in self._subscribers.items():
                logger.debug(f'Notifying subscriber {key} of summary action')
                asyncio.create_task(fn(summary_action))
                logger.debug(f'Notifying subscriber {key} of summary observation')
                asyncio.create_task(fn(summary_observation))
