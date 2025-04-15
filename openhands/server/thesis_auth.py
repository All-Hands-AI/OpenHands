import json
import os
from fastapi import Request, HTTPException
import requests
from openhands.core.logger import openhands_logger as logger


def get_user_detail_from_thesis_auth_server(bearer_token: str) -> dict | None:
    url = f"{os.getenv('THESIS_AUTH_SERVER_URL')}/api/users/detail"

    payload = {}
    headers = {
        'content-type': 'application/json',
        'Authorization': f'{bearer_token}'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    user = response.json()['user']
    return user

def add_invite_code_to_user(code: str, bearer_token: str) -> dict | None:
    try:
        url = f"{os.getenv('THESIS_AUTH_SERVER_URL')}/api/users/add-invite-code"
        payload = json.dumps({"code": code})
        headers = {
            'content-type': 'application/json',
            'Authorization': bearer_token
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        
        # Check if request was successful
        if response.status_code != 200:
            logger.error(f"Failed to add invite code: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to add invite code: {response.text}"
            )
            
        return response.json()
        
    except Exception as e:
        logger.error(f"Unexpected error while adding invite code: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while adding invite code: {str(e)}"
        ) 
