import asyncio
import json
import os
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from openhands.core.logger import openhands_logger as logger

# Import MemoryClient if not already imported
try:
    from mem0 import MemoryClient
except ImportError:
    # Fallback or raise error if not available
    MemoryClient = None


class Mem0MetadataType(Enum):
    FINISH_CONCLUSION = 'finish_conclusion'
    REPORT_FILE = 'report_file'


client = MemoryClient(api_key=os.getenv('MEM0_API_KEY'))


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

    if MemoryClient is None:
        logger.warning('MemoryClient is not available. Skipping mem0 add.')
        return parsed_events

    logger.info(f'duongtd_parsed_events: {parsed_events}')
    if parsed_events:
        add_result = await asyncio.to_thread(
            client.add,
            agent_id=conversation_id,
            messages=parsed_events,
            metadata=metadata,
            infer=True,
        )
        print(f'duongtd_add_mem0_result: {add_result}')
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
    if MemoryClient is None:
        logger.warning('MemoryClient is not available. Skipping mem0 search.')
        return None

    for meta_type in [Mem0MetadataType.REPORT_FILE, Mem0MetadataType.FINISH_CONCLUSION]:
        try:
            memories = client.search(
                query=question,
                agent_id=raw_followup_conversation_id,
                metadata={'type': meta_type.value},
                infer=True,
                top_k=10,
                keyword_search=True,
            )
            if memories:
                memory_id = memories[0]['id']
                histories = client.history(memory_id)
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
