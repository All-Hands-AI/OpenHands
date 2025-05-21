from typing import Callable

from openhands.core.config import load_app_config


def _json_serialize(data):
    """Converts data to a JSON-serializable format.

    Args:
        data: The data to convert. Can be any type.

    Returns:
        A JSON-serializable representation of the data.
    """
    if data is None:
        return None
    elif isinstance(data, (str, int, float, bool)):
        return data
    elif isinstance(data, (list, tuple)):
        return [_json_serialize(item) for item in data]
    elif isinstance(data, dict):
        return {str(k): _json_serialize(v) for k, v in data.items()}
    elif hasattr(data, 'to_dict') and callable(data.to_dict):
        return _json_serialize(data.to_dict())
    elif hasattr(data, '__dict__'):
        serialized = {}
        for attr_name, attr_value in data.__dict__.items():
            if not attr_name.startswith('_'):
                serialized[attr_name] = _json_serialize(attr_value)
        return serialized
    else:
        return str(data)


async def should_step_after_call_evaluation_endpoint(
    session_id: str,
    log_func: Callable[[str, str], None],
) -> tuple[bool, str]:
    """
    Call the evaluation endpoint synchronously to check if the agent should proceed with finishing.

    Args:
        session_id: The ID of the current session
        log_func: Function to log messages

    Returns:
        bool: True if the agent should finish, False if it should continue
    """
    config = load_app_config()
    evaluation_endpoint = config.evaluation_endpoint_url
    if not evaluation_endpoint:
        log_func('error', 'evaluation_endpoint_url not set in config.toml')
        return True, ''

    payload = {'session_id': session_id, 'action': 'should_step'}
    log_func(
        'info', f'Calling evaluation endpoint for validation: {evaluation_endpoint}'
    )

    headers = {'Content-Type': 'application/json'}

    try:
        from httpx import request

        response = request(
            method='POST',
            url=evaluation_endpoint,
            headers=headers,
            json=payload,
            timeout=5.0,
        )

        log_func('info', f'Evaluation endpoint response: {response.status_code}')

        try:
            response_data = response.json()
            log_data = _json_serialize(response_data)
            log_func('info', f'Evaluation validation response: {log_data}')

            should_proceed = response_data.get('result', True)
            log_func('info', f'Should proceed with finish action: {should_proceed}')

            reason = response_data.get('reason', '')

            return should_proceed, reason

        except Exception as e:
            log_func('error', f'Failed to parse JSON response: {str(e)}')
            return True, ''
    except Exception as e:
        log_func('error', f'Failed to call evaluation endpoint: {str(e)}')
        return True, ''
