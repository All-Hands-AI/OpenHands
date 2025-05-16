import asyncio
import json
import os
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

import asyncpg
from mem0 import MemoryClient

from openhands.core.logger import openhands_logger as logger


class Mem0MetadataType(Enum):
    FINISH_CONCLUSION = 'finish_conclusion'
    REPORT_FILE = 'report_file'


class DBConnectionPool:
    """
    Singleton class for managing database connections.
    Uses connection pooling to efficiently handle database operations.
    """

    _instance = None
    _pool = None
    _initializing = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBConnectionPool, cls).__new__(cls)
        return cls._instance

    async def init_pool(self):
        """Initialize the connection pool asynchronously if not already initialized."""
        if self._pool is None and not self._initializing:
            try:
                self._initializing = True

                # Get database connection info from environment
                user = os.getenv('POSTGRES_USER')
                password = os.getenv('POSTGRES_PASSWORD')
                database = os.getenv('POSTGRES_DB')
                host = os.getenv('POSTGRES_HOST', 'localhost')
                port = os.getenv('POSTGRES_PORT', '5432')

                # Create a connection pool
                self._pool = await asyncpg.create_pool(
                    user=user,
                    password=password,
                    database=database,
                    host=host,
                    port=port,
                    min_size=2,
                    max_size=10,
                )
                logger.info('Database connection pool initialized successfully')
            except Exception as e:
                logger.error(f'Failed to initialize connection pool: {str(e)}')
                self._pool = None
            finally:
                self._initializing = False

        return self._pool

    async def get_connection(self):
        """Get a connection from the pool."""
        pool = await self.init_pool()
        if pool:
            return await pool.acquire()
        return None

    async def release_connection(self, conn):
        """Return a connection to the pool."""
        if self._pool and conn:
            await self._pool.release(conn)

    async def close_pool(self):
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None


_db_pool_instance = DBConnectionPool()


class Mem0Client:
    """
    Singleton wrapper for MemoryClient to ensure a single instance is used across the application.
    Lazily initialized on first use.
    """

    _instance = None
    _client = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Mem0Client, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not Mem0Client._initialized:
            self._initialize_client()

    def _initialize_client(self):
        mem0_api_key = os.getenv('MEM0_API_KEY')
        api_key = mem0_api_key if mem0_api_key else 'placeholder_api_key'
        try:
            Mem0Client._client = MemoryClient(api_key=api_key)
            logger.info('MemoryClient initialized successfully')
            # Only set initialized to True when client is successfully created
            Mem0Client._initialized = True
        except Exception as e:
            logger.error(f'Failed to initialize MemoryClient: {e}')
            Mem0Client._client = None

    @property
    def client(self):
        return Mem0Client._client

    @property
    def is_available(self) -> bool:
        return Mem0Client._client is not None

    def add(self, *args, **kwargs):
        if not self.is_available:
            logger.warning('MemoryClient not available. Skipping add operation.')
            return None
        return self.client.add(*args, **kwargs)

    def search(self, *args, **kwargs):
        if not self.is_available:
            logger.warning('MemoryClient not available. Skipping search operation.')
            return []
        return self.client.search(*args, **kwargs)

    def history(self, *args, **kwargs):
        if not self.is_available:
            logger.warning('MemoryClient not available. Skipping history operation.')
            return []
        return self.client.history(*args, **kwargs)


def _extract_content_from_event(event: dict) -> Optional[str]:
    """Extracts the main content from an event, checking message, args.content, then content."""
    content = event.get('message')
    if not content:
        args = event.get('args')
        if args and isinstance(args, dict):
            content = args.get('content')
    if not content:
        content = event.get('content')
    return content


def _extract_file_text_from_tool_call(tool_calls: list) -> Optional[str]:
    """Extracts file_text from the first tool_call's function.arguments, if present and valid JSON."""
    if tool_calls and 'function' in tool_calls[0]:
        arguments_str = tool_calls[0]['function'].get('arguments')
        if arguments_str:
            try:
                arguments_json = json.loads(arguments_str)
                return arguments_json.get('file_text') or arguments_str
            except Exception as e:
                logger.warning(f'Failed to parse arguments as JSON: {e}')
                return arguments_str
    return None


async def _add_mem0_conversation_job_direct_db(
    conversation_id: str, events: List[Dict[str, Any]], metadata: Dict[str, Any]
) -> bool:
    """
    Add mem0 conversation job directly to the database using the connection pool.
    This avoids event loop conflicts by using a dedicated connection.
    """
    conn = None

    try:
        # Get connection from pool
        conn = await _db_pool_instance.get_connection()
        if not conn:
            logger.error('Failed to get database connection from pool')
            return False

        # Insert directly with asyncpg
        await conn.execute(
            """
            INSERT INTO mem0_conversation_jobs
            (conversation_id, events, metadata, status)
            VALUES ($1, $2, $3, $4)
            """,
            conversation_id,
            json.dumps(events),
            json.dumps(metadata),
            'pending',
        )
        return True
    except Exception as e:
        logger.error(f'Error adding mem0 conversation job directly: {str(e)}')
        return False
    finally:
        # Always release the connection back to the pool
        if conn:
            await _db_pool_instance.release_connection(conn)


async def process_single_event_for_mem0(
    conversation_id: str, event: dict
) -> List[Dict[str, Any]]:
    """
    Processes a single event dict and returns a list of mem0 events in the format {role, content}.
    Also adds the parsed events to mem0 in the background (non-blocking).
    """
    parsed_events: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {'chunk_id': str(uuid.uuid4())}
    source = event.get('source')
    action = event.get('action')
    observation = event.get('observation')
    content = _extract_content_from_event(event)

    if (
        not content
        and not (source == 'agent' and observation == 'edit')
        and action != 'finish'
    ):
        return []

    if source == 'user':
        parsed_events.append({'role': 'user', 'content': content})
    elif source == 'agent':
        if observation == 'mcp':
            return []
        elif observation == 'edit':
            tool_call_metadata = event.get('tool_call_metadata', {})
            model_response = tool_call_metadata.get('model_response', {})
            choices = model_response.get('choices', [])
            if choices and 'message' in choices[0]:
                message_obj = choices[0]['message']
                # First event: content
                edit_content = message_obj.get('content')
                if edit_content:
                    parsed_events.append({'role': 'assistant', 'content': edit_content})
                # Second event: tool_calls[0].function.arguments (extract file_text)
                file_text = _extract_file_text_from_tool_call(
                    message_obj.get('tool_calls', [])
                )
                if file_text:
                    parsed_events.append({'role': 'assistant', 'content': file_text})
                metadata['type'] = Mem0MetadataType.REPORT_FILE.value
        elif action == 'finish':
            tool_call_metadata = event.get('tool_call_metadata', {})
            model_response = tool_call_metadata.get('model_response', {})
            choices = model_response.get('choices', [])
            if choices and 'message' in choices[0]:
                message_obj = choices[0]['message']
                file_text = _extract_file_text_from_tool_call(
                    message_obj.get('tool_calls', [])
                )
                if file_text:
                    parsed_events.append({'role': 'assistant', 'content': file_text})
                metadata['type'] = Mem0MetadataType.FINISH_CONCLUSION.value
        # else:  # If you want to handle other agent cases, add here
        #     parsed_events.append({'role': 'assistant', 'content': content})

    # mem0_client = Mem0Client()
    # if not mem0_client.is_available:
    #     logger.warning('MemoryClient is not available. Skipping mem0 add.')
    #     return parsed_events

    logger.info(f'duongtd_parsed_events: {parsed_events}')
    if parsed_events:
        try:
            print('vap day vao day 2 metadata', metadata)
            # Use a separate task to write to the database to avoid event loop conflicts
            # This creates a fire-and-forget task that won't block the main execution
            asyncio.create_task(
                _add_mem0_conversation_job_direct_db(
                    conversation_id=conversation_id,
                    events=parsed_events,
                    metadata=metadata,
                )
            )
        except Exception as e:
            logger.error(f'Failed to add mem0 conversation job: {e}')
            return parsed_events

    return parsed_events


async def search_knowledge_mem0(
    question: Optional[str] = None,
    space_id: Optional[int] = None,
    raw_followup_conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Optional[List[dict]]:
    """
    Search mem0 for knowledge chunks related to the question and conversation.
    Tries both REPORT_FILE and FINISH_CONCLUSION types. Returns a list of knowledge dicts, each with a chunkId, or None if not found.
    """
    mem0_client = Mem0Client()
    if not mem0_client.is_available:
        logger.warning('MemoryClient is not available. Skipping mem0 search.')
        return None

    agent_id = raw_followup_conversation_id

    for meta_type in [Mem0MetadataType.REPORT_FILE, Mem0MetadataType.FINISH_CONCLUSION]:
        try:
            memories = mem0_client.search(
                query=question,
                agent_id=agent_id,
                metadata={'type': meta_type.value},
                infer=True,
                top_k=10,
                keyword_search=True,
            )
            if memories:
                memory_id = memories[0]['id']
                histories = mem0_client.history(memory_id)
                if histories:
                    knowledge = histories[0]['input']
                    chunk_id = histories[0]['metadata'].get(
                        'chunk_id', str(uuid.uuid4())
                    )
                    return [{**k, 'chunkId': chunk_id} for k in knowledge]
        except Exception:
            logger.exception(
                f'Unexpected error while searching knowledge for type {meta_type}'
            )
    return None


# Initialize DB connection pool on module import
# This will ensure the pool is created at startup


# async def retrieve_conversation_and_embedding_mem0(
#     conversation_id: str,
# ) -> list[dict]:
#     """
#     Fetches conversation events and returns a list of {role, content} dicts.
#     Only includes agent events if they do not have observation == 'mcp'.
#     """
#     url = f"http://localhost:3015/api/options/conversations/events/{conversation_id}"
#     headers = {
#         'Content-Type': 'application/json',
#         'x-key-oh': os.getenv('KEY_THESIS_BACKEND_SERVER'),
#     }

#     try:
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             response = await client.get(url, headers=headers)
#             if response.status_code != 200:
#                 logger.error(
#                     f'Failed to fetch conversation events: {response.status_code} - {response.text}'
#                 )
#                 raise HTTPException(
#                     status_code=response.status_code, detail=response.text
#                 )
#             events = response.json()
#             parsed_events = []
#             for event in events:
#                 source = event.get("source")
#                 action = event.get("action")
#                 # Prefer 'message', fallback to 'args.content', then 'content'
#                 content = event.get("message")
#                 if not content:
#                     args = event.get("args")
#                     if args and isinstance(args, dict):
#                         content = args.get("content")
#                 if not content:
#                     content = event.get("content")
#                 if (
#                     not content
#                     and not (source == "agent" and event.get("observation") == "edit")
#                     and action != "finish"
#                 ):
#                     continue  # skip if no content unless it's an edit or finish event
#                 if source == "user":
#                     parsed_events.append({"role": "user", "content": content})
#                 elif source == "agent":
#                     observation = event.get("observation")
#                     if observation == "mcp":
#                         continue
#                     elif observation == "edit":
#                         # Add two events for edit: message content and tool_call arguments
#                         tool_call_metadata = event.get("tool_call_metadata", {})
#                         model_response = tool_call_metadata.get("model_response", {})
#                         choices = model_response.get("choices", [])
#                         if choices and "message" in choices[0]:
#                             message_obj = choices[0]["message"]
#                             # First event: content
#                             edit_content = message_obj.get("content")
#                             if edit_content:
#                                 parsed_events.append(
#                                     {"role": "assistant", "content": edit_content}
#                                 )
#                             # Second event: tool_calls[0].function.arguments
#                             tool_calls = message_obj.get("tool_calls", [])
#                             if tool_calls and "function" in tool_calls[0]:
#                                 arguments = tool_calls[0]["function"].get("arguments")
#                                 if arguments:
#                                     parsed_events.append(
#                                         {"role": "assistant", "content": arguments}
#                                     )
#                         continue  # skip the normal agent append for edit
#                     elif action == "finish":
#                         # Add event for finish: tool_call arguments
#                         tool_call_metadata = event.get("tool_call_metadata", {})
#                         model_response = tool_call_metadata.get("model_response", {})
#                         choices = model_response.get("choices", [])
#                         if choices and "message" in choices[0]:
#                             message_obj = choices[0]["message"]
#                             tool_calls = message_obj.get("tool_calls", [])
#                             if tool_calls and "function" in tool_calls[0]:
#                                 arguments = tool_calls[0]["function"].get("arguments")
#                                 if arguments:
#                                     parsed_events.append(
#                                         {"role": "assistant", "content": arguments}
#                                     )
#                         continue  # skip the normal agent append for finish
#                     parsed_events.append({"role": "assistant", "content": content})

#             client = MemoryClient(api_key=os.getenv('MEM0_API_KEY'))

#             logger.info(f'duongtd_parsed_events: {parsed_events}')

#             add_result = client.add(
#                 messages=parsed_events,
#                 user_id=conversation_id,
#                 agent_id="openhands",
#                 metadata={},
#             )
#             print(f'duongtd_add_mem0_result: {add_result}')

#     except Exception as e:
#         logger.error('Unexpected error while fetching conversation events')
#         raise HTTPException(status_code=500, detail=str(e))
