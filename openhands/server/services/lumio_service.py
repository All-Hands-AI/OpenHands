import httpx
from openhands.core.logger import openhands_logger as logger


class LumioService:
    """Service for interacting with Lumio blockchain API."""

    def __init__(self, rpc_url: str, contract_address: str):
        self.rpc_url = rpc_url.rstrip('/')
        self.contract_address = contract_address

    async def is_whitelisted(self, user_address: str) -> bool:
        """Check if a user address is whitelisted in the vibe-balance contract.

        Args:
            user_address: The user's wallet address (hex string with or without 0x prefix)

        Returns:
            True if the user is whitelisted, False otherwise
        """
        if not self.contract_address:
            logger.warning('VIBE_BALANCE_CONTRACT not configured, skipping whitelist check')
            return True

        # Normalize address format
        if not user_address.startswith('0x'):
            user_address = f'0x{user_address}'

        url = f'{self.rpc_url}/v1/view'
        payload = {
            'function': f'{self.contract_address}::vibe_balance::is_whitelisted',
            'type_arguments': [],
            'arguments': [user_address],
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                result = response.json()
                # The result should be [true] or [false]
                if isinstance(result, list) and len(result) > 0:
                    return bool(result[0])
                return False
        except httpx.HTTPStatusError as e:
            logger.error(f'Lumio API HTTP error: {e.response.status_code} - {e.response.text}')
            return False
        except httpx.RequestError as e:
            logger.error(f'Lumio API request error: {e}')
            return False
        except Exception as e:
            logger.error(f'Unexpected error checking whitelist: {e}')
            return False

    async def get_balance(self, user_address: str) -> int:
        """Get user's balance from the vibe-balance contract.

        Args:
            user_address: The user's wallet address

        Returns:
            User's balance as integer, 0 if not found or error
        """
        if not self.contract_address:
            logger.warning('VIBE_BALANCE_CONTRACT not configured')
            return 0

        if not user_address.startswith('0x'):
            user_address = f'0x{user_address}'

        url = f'{self.rpc_url}/v1/view'
        payload = {
            'function': f'{self.contract_address}::vibe_balance::get_balance',
            'type_arguments': [],
            'arguments': [user_address],
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return int(result[0])
                return 0
        except Exception as e:
            logger.error(f'Error getting balance: {e}')
            return 0
