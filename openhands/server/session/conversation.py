import asyncio
import base64
import pickle
import json

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.stream import EventStream
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.security import SecurityAnalyzer, options
from openhands.storage.files import FileStore
from openhands.storage.locations import get_conversation_agent_state_filename, get_conversation_dir
from openhands.utils.async_utils import call_sync_from_async
from openhands.controller.state.state import State


class Conversation:
    sid: str
    file_store: FileStore
    event_stream: EventStream
    runtime: Runtime
    user_id: str | None

    def __init__(
        self, sid: str, file_store: FileStore, config: AppConfig, user_id: str | None
    ):
        self.sid = sid
        self.config = config
        self.file_store = file_store
        self.user_id = user_id

        last_event_id = -1
        state_filename = get_conversation_agent_state_filename(sid, user_id)
        log_filename = f'{get_conversation_dir(sid, user_id)}events.jsonl'

        try:
            logger.info(f'Attempting to read state file: {state_filename}')
            encoded = file_store.read(state_filename)
            pickled = base64.b64decode(encoded)
            state_obj = pickle.loads(pickled)

            if isinstance(state_obj, State):
                last_event_id = getattr(state_obj, '_last_event_id', -1)
                logger.info(f'Read state object for {sid}. Found _last_event_id: {last_event_id}')
            else:
                logger.warning(f'Loaded state for {sid} is not a State object. Type: {type(state_obj)}. Cannot retrieve last_event_id.')
                last_event_id = -1
        except FileNotFoundError:
            logger.warning(f'State file {state_filename} not found for {sid}. Attempting fallback from events log.')
            try:
                logger.info(f'Attempting fallback read from: {log_filename}')
                full_content = file_store.read(log_filename)
                lines = full_content.splitlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        try:
                            last_event_data = json.loads(last_line)
                            if isinstance(last_event_data, dict) and 'id' in last_event_data and isinstance(last_event_data['id'], int):
                                last_event_id = last_event_data['id']
                                logger.info(f'Fallback successful. Determined last_event_id from log: {last_event_id}')
                            else:
                                logger.warning(f'Last line of log {log_filename} is not a valid event JSON with an ID.')
                                last_event_id = -1
                        except json.JSONDecodeError:
                            logger.warning(f'Failed to decode last line of log {log_filename} as JSON.')
                            last_event_id = -1
                    else:
                        logger.info(f'Log file {log_filename} exists but last line is empty.')
                        last_event_id = -1
                else:
                    logger.info(f'Log file {log_filename} exists but is empty.')
                    last_event_id = -1
            except FileNotFoundError:
                logger.info(f'Fallback failed. Log file {log_filename} also not found. Assuming new session.')
                last_event_id = -1
            except Exception as log_err:
                logger.error(f'Error during fallback read of {log_filename}: {log_err}')
                last_event_id = -1
        except Exception as e:
            logger.error(f'Error reading or parsing state file {state_filename} for {sid}: {e}')
            last_event_id = -1

        initial_cur_id = last_event_id + 1 if last_event_id >= 0 else -1
        logger.info(f'Initializing EventStream for {sid} with initial cur_id: {initial_cur_id} (derived from last_event_id: {last_event_id})')
        self.event_stream = EventStream(sid, file_store, user_id, cur_id=initial_cur_id)

        if config.security.security_analyzer:
            self.security_analyzer = options.SecurityAnalyzers.get(
                config.security.security_analyzer, SecurityAnalyzer
            )(self.event_stream)

        runtime_cls = get_runtime_cls(self.config.runtime)
        self.runtime = runtime_cls(
            config=config,
            event_stream=self.event_stream,
            sid=self.sid,
            attach_to_existing=True,
            headless_mode=False,
        )

    async def connect(self):
        await self.runtime.connect()

    async def disconnect(self):
        if self.event_stream:
            self.event_stream.close()
        asyncio.create_task(call_sync_from_async(self.runtime.close))
