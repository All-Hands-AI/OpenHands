from uuid import uuid4

from openhands.runtime.plugins.agent_skills.a2a_client.common.client import (
    A2ACardResolver,
    A2AClient,
)
from openhands.runtime.plugins.agent_skills.a2a_client.common.types import (
    TaskState,
)


async def send_task_A2A(url, message, session_id=0, task_id=0):
    """
    Send a task to an agent hosted on remote server, compatible with A2A protocol.
    """
    ## Get the agent card
    card_resolver = A2ACardResolver(url)
    card = card_resolver.get_agent_card()

    print('======= Agent Card ========')
    print(card.model_dump_json(exclude_none=True))

    client = A2AClient(agent_card=card)

    if session_id == 0:
        session_id = uuid4().hex
    if task_id == 0:
        task_id = uuid4().hex

    streaming = card.capabilities.streaming
    print('======= Session ID and Task ID ========')
    print(f'Session ID: {session_id}')
    print(f'Task ID: {task_id}')
    print('If you want to send more input, use the same session ID and task ID.')

    print('=========  starting a task ======== ')
    await completeTask(client, message, streaming, task_id, session_id)


async def completeTask(client: A2AClient, message, streaming, task_id, session_id):
    prompt = message

    message = {
        'role': 'user',
        'parts': [
            {
                'type': 'text',
                'text': prompt,
            }
        ],
    }

    payload = {
        'id': task_id,
        'sessionId': session_id,
        'acceptedOutputModes': ['text'],
        'message': message,
    }

    taskResult = None
    if streaming:
        response_stream = client.send_task_streaming(payload)
        async for result in response_stream:
            print(f'stream event => {result.model_dump_json(exclude_none=True)}')
        taskResult = await client.get_task({'id': task_id})
    else:
        taskResult = await client.send_task(payload)
        print(f'\n{taskResult.model_dump_json(exclude_none=True)}')

    ## if the result is that more input is required, tell the user and exit.
    if taskResult.result:
        state = TaskState(taskResult.result.status.state)
        if state.name == TaskState.INPUT_REQUIRED.name:
            print('Task requires more input. Use this tool again to provide it.')
        else:
            ## task is complete
            return True


__all__ = ['send_task_A2A']
