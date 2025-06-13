import os
import time
from enum import Enum, IntEnum

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, status
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.research import ResearchMode

load_dotenv()


class UserStatus(IntEnum):
    INACTIVE = 0
    ACTIVE = 1
    WHITELISTED = 1
    BLACKLISTED = 0


class FeatureCode(Enum):
    FOLLOW_UP = ('follow_up',)
    WEBSEARCH = ('websearch',)
    DEEP_RESEARCH = ('deep_research',)
    DISCOVER_PUBLISHING = ('discover_publishing',)
    SPACES = ('spaces',)
    AUTONOMOUS_EXECUTION = ('autonomous_execution',)
    MULTI_AGENTS = 'multi_agents'


class ThesisUser(BaseModel):
    status: UserStatus
    whitelisted: int
    publicAddress: str
    mnemonic: str
    solanaThesisAddress: str | None = None
    ethThesisAddress: str | None = None
    # Add other fields as needed


thesis_auth_client = httpx.AsyncClient(
    timeout=30.0,
    base_url=os.getenv('THESIS_AUTH_SERVER_URL', ''),
    headers={'Content-Type': 'application/json'},
)


async def get_user_detail_from_thesis_auth_server(
    bearer_token: str,
    x_device_id: str | None = None,
) -> ThesisUser | None:
    # TODO: bypass auth server for dev mode
    if os.getenv('RUN_MODE') == 'DEV':
        return ThesisUser(
            status=UserStatus.ACTIVE,
            whitelisted=1,
            publicAddress='0x25bE302C3954b4DF9F67AFD6BfDD8c39f4Dc98Dc',
            mnemonic='test test test test test test test test test test junk',
            solanaThesisAddress='0x25bE302C3954b4DF9F67AFD6BfDD8c39f4Dc98Dc',
            ethThesisAddress='0x25bE302C3954b4DF9F67AFD6BfDD8c39f4Dc98Dc',
        )

    url = '/api/users/detail'
    headers = {'Content-Type': 'application/json', 'Authorization': bearer_token}
    if x_device_id:
        headers['x-device-id'] = x_device_id
    try:
        start_time = time.time()
        response = await thesis_auth_client.get(url, headers=headers)
        end_time = time.time()
        logger.info(f'Time taken to get user detail: {end_time - start_time} seconds')
    except httpx.RequestError as exc:
        logger.error(f'Request error while getting user detail: {exc}')
        raise HTTPException(status_code=500, detail='Unable to reach auth server')

    if response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(
            f'Failed to get user detail: {response.status_code} - {response.text}'
        )
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get('error', 'Unknown error'),
        )

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        logger.error(
            f'Failed to get user detail: {response.status_code} - {response.text}'
        )
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get('error', f'Unauthorized : {response.text}'),
        )
    user_data = response.json().get('user')
    if not user_data:
        return None

    return ThesisUser(**user_data)


async def add_invite_code_to_user(
    code: str, bearer_token: str, x_device_id: str | None = None
) -> dict | None:
    url = '/api/users/add-invite-code'
    payload = {'code': code}
    headers = {'Content-Type': 'application/json', 'Authorization': bearer_token}
    if x_device_id:
        headers['x-device-id'] = x_device_id
    try:
        response = await thesis_auth_client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(
                f'Failed to add invite code: {response.status_code} - {response.text}'
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get('error', 'Unknown error'),
            )

        return response.json()

    except httpx.RequestError as exc:
        logger.error(f'Request error while adding invite code: {str(exc)}')
        raise HTTPException(status_code=500, detail='Could not connect to auth server')
    except Exception as e:
        logger.exception('Unexpected error while adding invite code')
        raise HTTPException(status_code=500, detail=str(e))


async def handle_api_response(response, operation_name):
    """
    Process the response from the API
    """
    if response.status_code >= 400:
        error_message = f'{operation_name} failed: {response.status_code}'
        try:
            error_detail = response.json().get('error', 'Unknown error')
            if isinstance(error_detail, dict) and 'message' in error_detail:
                error_detail = error_detail['message']
        except Exception:
            error_detail = response.text or 'Unknown error'

        logger.error(f'{error_message} - {error_detail}')

        # Return the correct status code from the API
        raise HTTPException(
            status_code=response.status_code,
            detail=error_detail,
        )


async def handle_thesis_auth_request(
    method: str,
    endpoint: str,
    bearer_token: str,
    payload: dict | None = None,
    params: dict | None = None,
    x_device_id: str | None = None,
) -> dict:
    url = f'{endpoint}'
    headers = {'Content-Type': 'application/json', 'Authorization': bearer_token}
    if x_device_id:
        headers['x-device-id'] = x_device_id
    try:
        response = await thesis_auth_client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=payload,  # use json= instead of data=
            params=params,
        )

        await handle_api_response(response, f'Thesis_auth request {method} {endpoint}')
        return response.json()

    except httpx.RequestError as exc:
        logger.error(
            f'Connection error in Thesis_auth request: {method} {endpoint} {str(exc)}'
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Unable to connect to auth server',
        )

    except Exception as e:
        logger.exception(
            f'Unexpected error in Thesis_auth request: {method} {endpoint}'
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(getattr(e, 'detail', 'Internal server error')),
        )


def check_access_token_in_header(request):
    authorization = request.headers.get('Authorization')
    if not authorization:
        logger.error('Access token not found in request headers')
        raise HTTPException(
            status_code=401, detail='Unauthorized: Access token is required'
        )

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != 'bearer':
        logger.error("Invalid authorization format. Expected 'Bearer <token>'")
        raise HTTPException(
            status_code=401, detail='Unauthorized: Invalid token format'
        )


async def create_thread(
    space_id: int | None = None,
    follow_up_id: int | None = None,
    conversation_id: str | None = None,
    initial_user_msg: str | None = None,
    bearer_token: str | None = None,
    x_device_id: str | None = None,
    followup_discover_id: str | None = None,
    research_mode: str | None = None,
) -> dict | None:
    url = '/api/threads'
    payload = {'conversationId': conversation_id, 'prompt': initial_user_msg}
    headers = {'Content-Type': 'application/json', 'Authorization': bearer_token}

    if x_device_id:
        headers['x-device-id'] = x_device_id
    if space_id is not None:
        payload['spaceId'] = str(space_id)

    if follow_up_id is not None:
        payload['forkById'] = str(follow_up_id)
    if followup_discover_id is not None:
        payload['followupDiscoverId'] = followup_discover_id
    if research_mode is not None and research_mode == ResearchMode.FOLLOW_UP:
        payload['researchMode'] = research_mode
    try:
        response = await thesis_auth_client.post(url, headers=headers, json=payload)
        await handle_api_response(response, 'Create thread')
        return response.json()
    except httpx.RequestError as exc:
        logger.error(f'Connection error creating thread: {str(exc)}')
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Could not connect to thread server',
        )
    except Exception as e:
        logger.exception('Unexpected error creating thread')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def search_knowledge(
    question: str | None = None,
    space_id: int | None = None,
    thread_follow_up: int | None = None,
    user_id: str | None = None,
) -> list[dict] | None:
    url = '/api/knowledge/search'
    payload = {'question': question}
    if space_id is not None:
        payload['spaceId'] = str(space_id)
    if thread_follow_up:
        payload['threadId'] = str(thread_follow_up)
    if user_id:
        payload['publicAddress'] = user_id

    headers = {
        'Content-Type': 'application/json',
        'x-key-oh': os.getenv('KEY_THESIS_BACKEND_SERVER'),
    }
    logger.debug(f'payload: {payload}')
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            base_url=os.getenv('THESIS_AUTH_SERVER_URL', ''),
            headers={'Content-Type': 'application/json'},
        ) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            logger.error(
                f'Failed to search knowledge: {response.status_code} - {response.text}'
            )
            return None
        data = response.json()['data']
        print(f'Data search knowledge: {data}')
        if data:
            return data['knowledge']
        else:
            return None
    except httpx.RequestError as exc:
        logger.error(f'Request error while searching knowledge: {str(exc)}')
        return None
        # raise HTTPException(
        #     status_code=500, detail='Could not connect to knowledge server'
        # )
    except Exception:
        logger.error('Unexpected error while searching knowledge')
        return None


async def webhook_rag_conversation(
    conversation_id: str,
) -> bool:
    url = '/api/threads/webhook/rag-job'
    payload = {'conversationId': conversation_id}
    headers = {
        'Content-Type': 'application/json',
        'x-key-oh': os.getenv('KEY_THESIS_BACKEND_SERVER'),
    }
    try:
        async with httpx.AsyncClient(
            base_url=os.getenv('THESIS_AUTH_SERVER_URL', ''),
            timeout=30.0,
        ) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(
                    f'Failed to sync conversation to rag: {response.status_code} - {response.text}'
                )
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )
            return True
    except httpx.RequestError as exc:
        logger.error(f'Failed to sync conversation to rag: {str(exc)}')
        return False


async def delete_thread(
    conversation_id: str,
    bearer_token: str,
    x_device_id: str | None = None,
) -> dict | None:
    url = f'/api/threads/delete-thread-by-conversation-id/{conversation_id}'
    headers = {'Content-Type': 'application/json', 'Authorization': bearer_token}
    if x_device_id:
        headers['x-device-id'] = x_device_id
    try:
        response = await thesis_auth_client.delete(url, headers=headers)
        if response.status_code != 200:
            logger.error(
                f'Failed to delete thread: {response.status_code} - {response.text}'
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get('error', 'Unknown error'),
            )

        return response.json()
    except httpx.RequestError as exc:
        logger.error(f'Request error while deleting thread: {str(exc)}')
        raise HTTPException(status_code=500, detail='Could not connect to auth server')
    except Exception as e:
        logger.exception('Unexpected error while deleting thread')
        raise HTTPException(status_code=500, detail=str(e))


async def change_thread_visibility(
    conversation_id: str,
    is_published: bool,
    bearer_token: str,
    x_device_id: str | None = None,
) -> dict | None:
    url = f'/api/threads/change-visibility-by-conversation-id/{conversation_id}'
    payload = {'visibility': 0 if not is_published else 1}
    headers = {'Content-Type': 'application/json', 'Authorization': bearer_token}
    if x_device_id:
        headers['x-device-id'] = x_device_id
    try:
        response = await thesis_auth_client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(
                f'Failed to change thread visibility: {response.status_code} - {response.text}'
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get('error', 'Unknown error'),
            )

        return response.json()

    except httpx.RequestError as exc:
        logger.error(f'Request error while changing thread visibility: {str(exc)}')
        raise HTTPException(status_code=500, detail='Could not connect to auth server')
    except Exception as e:
        logger.exception('Unexpected error while changing thread visibility')
        raise HTTPException(status_code=500, detail=str(e))


async def get_thread_by_id(
    thread_id: int,
) -> dict | None:
    url = f'/api/threads/openhand-server/{thread_id}'
    headers = {
        'Content-Type': 'application/json',
        'x-key-oh': os.getenv('KEY_THESIS_BACKEND_SERVER'),
    }
    try:
        response = await thesis_auth_client.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(
                f'Failed to get thread: {response.status_code} - {response.text}'
            )
            return None
        data = response.json()['data']
        return data
    except httpx.RequestError as exc:
        logger.error(f'Request error while getting thread: {str(exc)}')
        return None


async def check_feature_credit(
    user_id: str, feature_code: str, run_on_oh: bool = False
) -> dict | None:
    url = '/api/subcription/check-pricing'
    headers = {
        'Content-Type': 'application/json',
        'x-key-oh': os.getenv('KEY_THESIS_BACKEND_SERVER'),
    }
    payload = {'featureCode': feature_code, 'userId': user_id}
    logger.debug(f'payload: {payload}')
    try:
        if run_on_oh:
            async with httpx.AsyncClient(
                base_url=os.getenv('THESIS_AUTH_SERVER_URL', ''),
                timeout=30.0,
            ) as client:
                response = await client.post(url, headers=headers, json=payload)
        else:
            response = await thesis_auth_client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(
                f'Failed to check feature credit: {response.status_code} - {response.text}'
            )
            if not run_on_oh:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get('msg', 'Unknown error'),
                )

        return response.json()
    except httpx.RequestError as exc:
        logger.error(f'Request error while check feature credit: {str(exc)}')
        raise HTTPException(status_code=500, detail='Could not connect to auth server')
    except Exception as e:
        logger.exception('Unexpected error while check feature credit')
        raise HTTPException(status_code=500, detail=str(e))
