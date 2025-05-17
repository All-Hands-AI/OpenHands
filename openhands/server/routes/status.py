"""API endpoints for conversation status information."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.events.serialization.event import event_to_dict
from openhands.llm.llm import LLM
from openhands.server.user_auth import get_user_settings
from openhands.storage.data_models.settings import Settings

app = APIRouter(prefix='/api/conversations/{conversation_id}/status')


async def get_settings(request: Request) -> Settings:
    """Get the settings for the current user."""
    settings = await get_user_settings(request)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Settings not found'
        )
    return settings


async def generate_status_field(events: list[Event], prompt: str, settings: Settings) -> str:
    """Generate a status field using the LLM.
    
    Args:
        events: List of events from the conversation
        prompt: The prompt to send to the LLM
        settings: User settings containing LLM configuration
        
    Returns:
        A string containing the generated status field
    """
    try:
        if not settings or not settings.llm_model:
            return "Unable to generate status: LLM not configured"
            
        # Create LLM config from settings
        llm_config = LLMConfig(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
        
        # Convert events to a format suitable for the LLM
        event_dicts = [event_to_dict(event) for event in events]
        conversation_text = "\n".join([
            f"{event.get('source', 'unknown')}: {event.get('content', '')}" 
            for event in event_dicts 
            if event.get('content')
        ])
        
        # Truncate if too long
        if len(conversation_text) > 10000:
            conversation_text = conversation_text[:10000] + "...(truncated)"
        
        # Create a prompt for the LLM
        messages = [
            {
                'role': 'system',
                'content': prompt,
            },
            {
                'role': 'user',
                'content': f'Here is the conversation:\n\n{conversation_text}',
            },
        ]
        
        # Get response from LLM
        llm = LLM(llm_config)
        response = llm.completion(messages=messages)
        result = response.choices[0].message.content.strip()
        
        return result
    except Exception as e:
        logger.error(f'Error generating status field: {e}')
        return f"Error generating status: {str(e)}"


@app.get('/intent')
async def get_intent(request: Request, settings: Settings = Depends(get_settings)) -> JSONResponse:
    """Get the intent of the conversation.
    
    This endpoint analyzes the conversation and returns a concise statement of the user's intent.
    
    Args:
        request: The incoming FastAPI request object
        settings: User settings containing LLM configuration
        
    Returns:
        JSONResponse: A JSON response containing the intent
    """
    try:
        if not request.state.conversation:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={'error': 'Conversation not found'}
            )
        
        # Get all events from the conversation
        event_stream = request.state.conversation.event_stream
        events = list(event_stream.get_events())
        
        # Generate the intent using the LLM
        prompt = """You are a helpful assistant that analyzes conversations between a user and OpenHands AI.
Your task is to identify and summarize the user's primary intent or goal in this conversation.
Provide a single, concise sentence (maximum 50 words) that clearly states what the user is trying to accomplish.
Focus only on the user's main objective, not on intermediate steps or implementation details.
Return only the intent statement, with no additional text, quotes, or explanations."""
        
        intent = await generate_status_field(events, prompt, settings)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK, 
            content={'intent': intent}
        )
    except Exception as e:
        logger.error(f'Error getting intent: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error getting intent: {e}'},
        )


@app.get('/definition-of-done')
async def get_definition_of_done(request: Request, settings: Settings = Depends(get_settings)) -> JSONResponse:
    """Get the definition of done for the conversation.
    
    This endpoint analyzes the conversation and returns a concise statement of what would constitute
    a successful completion of the user's request.
    
    Args:
        request: The incoming FastAPI request object
        settings: User settings containing LLM configuration
        
    Returns:
        JSONResponse: A JSON response containing the definition of done
    """
    try:
        if not request.state.conversation:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={'error': 'Conversation not found'}
            )
        
        # Get all events from the conversation
        event_stream = request.state.conversation.event_stream
        events = list(event_stream.get_events())
        
        # Generate the definition of done using the LLM
        prompt = """You are a helpful assistant that analyzes conversations between a user and OpenHands AI.
Your task is to define what would constitute a successful completion of the user's request.
Provide a single, concise sentence (maximum 50 words) that clearly states the criteria for considering the task complete.
Focus on measurable outcomes and specific deliverables that would satisfy the user's request.
Return only the definition of done statement, with no additional text, quotes, or explanations."""
        
        definition_of_done = await generate_status_field(events, prompt, settings)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK, 
            content={'definition_of_done': definition_of_done}
        )
    except Exception as e:
        logger.error(f'Error getting definition of done: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error getting definition of done: {e}'},
        )


@app.get('/current-status')
async def get_current_status(request: Request, settings: Settings = Depends(get_settings)) -> JSONResponse:
    """Get the current status of the conversation.
    
    This endpoint analyzes the conversation and returns a concise statement of the current progress
    towards completing the user's request.
    
    Args:
        request: The incoming FastAPI request object
        settings: User settings containing LLM configuration
        
    Returns:
        JSONResponse: A JSON response containing the current status
    """
    try:
        if not request.state.conversation:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={'error': 'Conversation not found'}
            )
        
        # Get all events from the conversation
        event_stream = request.state.conversation.event_stream
        events = list(event_stream.get_events())
        
        # Generate the current status using the LLM
        prompt = """You are a helpful assistant that analyzes conversations between a user and OpenHands AI.
Your task is to assess and summarize the current progress towards completing the user's request.
Provide a single, concise sentence (maximum 50 words) that clearly states what has been accomplished so far
and what remains to be done.
Focus on the current state of the task, major milestones achieved, and any significant challenges encountered.
Return only the current status statement, with no additional text, quotes, or explanations."""
        
        current_status = await generate_status_field(events, prompt, settings)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK, 
            content={'current_status': current_status}
        )
    except Exception as e:
        logger.error(f'Error getting current status: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error getting current status: {e}'},
        )