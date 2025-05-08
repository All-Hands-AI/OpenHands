import re
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openhands.core.config.llm_config import LLMConfig
from openhands.events.event import Event
from openhands.events.stream import EventStream
from openhands.llm.llm import LLM
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import file_store, conversation_manager
from openhands.server.user_auth import get_user_id, get_user_settings_store
from openhands.server.utils import get_conversation_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.settings.settings_store import SettingsStore

prompt_template = """
You are tasked with generating a prompt that will be used by another AI to update a special reference file. This file contains important information and learnings that are used to carry out certain tasks. The file can be extended over time to incorporate new knowledge and experiences.

You have been provided with a subset of new events that may require updates to the special file. These events are:
<events>
{{EVENTS}}
</events>

Your task is to analyze these events and determine what updates, if any, should be made to the special file. Then, you need to generate a prompt that will instruct another AI to make these updates correctly and efficiently.

When creating your prompt, follow these guidelines:
1. Clearly specify which parts of the file need to be updated or if new sections should be added.
2. Provide context for why these updates are necessary based on the new events.
3. Be specific about the information that should be added or modified.
4. Maintain the existing structure and formatting of the file.
5. Ensure that the updates are consistent with the current content and don't contradict existing information.

Now, based on the new events provided, generate a prompt that will guide the AI in making the appropriate updates to the special file. Your prompt should be clear, specific, and actionable. Include your prompt within <update_prompt> tags.

<update_prompt>

</update_prompt>
"""


def get_context_events(
        events: list[Event],
        event_id: int,
        context_size: int = 4,
) -> list[Event]:
    """
    Get a list of events around a specific event ID.

    Args:
        events: List of events to search through.
        event_id: The ID of the target event.
        context_size: Number of events to include before and after the target event.

    Returns:
        A list of events including the target event and the specified number of events before and after it.
    """
    target_event_index = None
    for i, event in enumerate(events):
        if event.id == event_id:
            target_event_index = i
            break
        
    if target_event_index is None:
        raise ValueError(f"Event with ID {event_id} not found in the event stream.")

    # Get X events around the target event
    start_index = max(0, target_event_index - context_size)
    end_index = min(len(events), target_event_index + context_size + 1) # +1 to include the target event

    return events[start_index:end_index]


def generate_prompt(llm_config: LLMConfig, events: str, prompt_template: str = prompt_template) -> str:
    llm = LLM(llm_config)
    messages = [
        {
            "role": "system",
            "content": prompt_template.replace("{{EVENTS}}", events),
        },
        {
            "role": "user",
            "content": "Please generate a prompt for the AI to update the special file based on the events provided.",
        },
    ]

    response = llm.completion(messages=messages)
    raw_prompt = response["choices"][0]["message"]["content"].strip()
    prompt = re.search(
        r"<update_prompt>(.*?)</update_prompt>", raw_prompt, re.DOTALL
    )

    if prompt:
        return prompt.group(1).strip()
    else:
        raise ValueError("No valid prompt found in the response.")


async def generate_unique_conversation_id(
        conversation_store: ConversationStore,
) -> str:
    conversation_id = uuid.uuid4().hex
    while await conversation_store.exists(conversation_id):
        conversation_id = uuid.uuid4().hex
    return conversation_id

app = APIRouter(prefix='/knowledge')

class KnowledgePromptRequest(BaseModel):
    conversation_id: str
    event_id: int


@app.get('/prompt/{conversation_id}')
async def get_prompt(
    update_request: KnowledgePromptRequest,
    user_id: str = Depends(get_user_id),
    user_settings: SettingsStore = Depends(get_user_settings_store),
):
    # get event stream for the conversation
    event_stream = EventStream(update_request.conversation_id, file_store, user_id)
    events = event_stream.get_events()

    # find the specified events to learn from
    context_events = get_context_events(list(events), update_request.event_id)
    stringified_events = "\n".join([str(event) for event in context_events])

    # generate a prompt
    settings = await user_settings.load()
    if settings is None:
        # placeholder for error handling
        raise ValueError("Settings not found")

    llm_config = LLMConfig(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )

    prompt = generate_prompt(llm_config, stringified_events)

    return JSONResponse(
        {
            "status": "success",
            "prompt": prompt,
        }
    )


class KnowledgeUpdateRequest(KnowledgePromptRequest):
    """
    Request to update the microagent with new learnings.
    """
    prompt: str | None = None


@app.post('/update')
async def update_knowledge(
    update_request: KnowledgePromptRequest,
    user_id: str = Depends(get_user_id),
    conversation_store: ConversationStore = Depends(get_conversation_store),
):
    """
    Update the microagent with new learnings through a conversation.
    """
    # get event stream for the conversation
    event_stream = EventStream(update_request.conversation_id, file_store, user_id)
    events = event_stream.get_events()

    # find the specified events to learn from
    context_events = get_context_events(list(events), update_request.event_id)
    stringified_events = "\n".join([str(event) for event in context_events])
    
    prompt = prompt_template.replace("{{EVENTS}}", stringified_events)

    # get existing conversation meta data
    metadata = await conversation_store.get_metadata(KnowledgePromptRequest.conversation_id)
    selected_repository = metadata.selected_repository

    # create a new conversation with the prompt
    conversation_init_data = ConversationInitData(
        # unload settings here too
        selected_repository=selected_repository,
        git_provider_tokens=None,
    )
    conversation_id = await generate_unique_conversation_id(conversation_store)

    conversation_metadata = ConversationMetadata(
            conversation_id=conversation_id,
            user_id=user_id,
            selected_repository=selected_repository,
            trigger=None, # should we create a trigger for this?
            title=None, # should we automatically generate a title?
            github_user_id=None,
            selected_branch=None,
        )

    await conversation_store.save_metadata(conversation_metadata)

    await conversation_manager.maybe_start_agent_loop(
        conversation_id,
        conversation_init_data,
        user_id,
        initial_user_msg=prompt,
    )

    # return the conversation id
    return JSONResponse(
        {
            "status": "job_created",
            "conversation_job_id": conversation_id,
        }
    )