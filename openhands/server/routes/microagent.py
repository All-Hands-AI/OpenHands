import re
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from openhands.core.config.llm_config import LLMConfig
from openhands.events.stream import EventStream
from openhands.llm.llm import LLM
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import conversation_manager
from openhands.server.user_auth import get_user_id, get_user_settings_store
from openhands.server.utils import generate_unique_conversation_id, get_context_events, get_conversation_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.settings.settings_store import SettingsStore

def generate_prompt_template(events: str) -> str:
    env = Environment(loader=FileSystemLoader('../../microagent/prompts'))
    template = env.get_template('generate_remember_prompt.j2')
    return template.render(events=events)


def generate_prompt(llm_config: LLMConfig, prompt_template: str) -> str:
    llm = LLM(llm_config)
    messages = [
        {
            "role": "system",
            "content": prompt_template,
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


app = APIRouter(prefix='/api/memory')

class KnowledgePromptRequest(BaseModel):
    conversation_id: str
    event_id: int

@app.get('/{conversation_id}/remember_prompt')
async def get_prompt(
    request: Request,
    update_request: KnowledgePromptRequest,
    user_settings: SettingsStore = Depends(get_user_settings_store),
):
    # get event stream for the conversation
    event_stream: EventStream = request.state.conversation.event_stream
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

    prompt_template = generate_prompt_template(stringified_events)
    prompt = generate_prompt(llm_config, prompt_template)

    return JSONResponse(
        {
            "status": "success",
            "prompt": prompt,
        }
    )


class MemoryUpdateRequest(KnowledgePromptRequest):
    """
    Request to update the microagent with new learnings.
    """
    prompt: str | None = None


@app.post('/update')
async def update_knowledge(
    request: Request,
    update_request: MemoryUpdateRequest,
    user_id: str = Depends(get_user_id),
    conversation_store: ConversationStore = Depends(get_conversation_store),
):
    """
    Update the microagent with new learnings through a conversation.
    """
    # get event stream for the conversation
    event_stream: EventStream = request.state.conversation.event_stream
    events = event_stream.get_events()

    # find the specified events to learn from
    context_events = get_context_events(list(events), update_request.event_id)
    stringified_events = "\n".join([str(event) for event in context_events])
    
    prompt = update_request.prompt or generate_prompt_template(stringified_events)

    # get existing conversation meta data
    metadata = await conversation_store.get_metadata(update_request.conversation_id)
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