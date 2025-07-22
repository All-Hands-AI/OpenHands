"""Tom API client for communicating with the Tom agent REST API."""

import json
from typing import Dict, Optional

import aiohttp

from openhands.core.logger import openhands_logger as logger


class TomApiClient:
    """HTTP client for Tom agent API communication."""

    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize the Tom API client.

        Args:
            base_url: Base URL of the Tom API server (e.g., "http://localhost:8000")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create the HTTP session."""
        try:
            # Check if the session is tied to the current event loop
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(timeout=self.timeout)
            # Verify the session's loop is the current loop
            elif self._session._loop is not None and self._session._loop.is_closed():
                # Session tied to a closed loop, create a new one
                self._session = aiohttp.ClientSession(timeout=self.timeout)
            return self._session
        except RuntimeError:
            # Event loop issues, create a fresh session
            self._session = aiohttp.ClientSession(timeout=self.timeout)
            return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def health_check(self) -> bool:
        """Check if the Tom API is healthy.

        Returns:
            True if the API is healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "healthy"
                return False
        except Exception as e:
            logger.debug(f"Tom API health check failed: {e}")
            return False

    async def propose_instructions(
        self, user_id: str, original_instruction: str, context: str
    ) -> Dict:
        """Get improved, personalized instructions from Tom.

        Args:
            user_id: Unique identifier for the user
            original_instruction: The original instruction from the user
            context: Full conversation context in LLM format

        Returns:
            API response dict containing recommendations or error info
        """
        try:
            url = f"{self.base_url}/propose_instructions"
            payload = {
                "user_id": user_id,
                "original_instruction": original_instruction,
                "context": context
            }

            logger.debug(f"Calling Tom API for instruction improvement: {url}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

            async with self.session.post(url, json=payload) as response:
                response_data = await response.json()

                if response.status == 200:
                    logger.debug(f"Tom instruction improvement successful: {response_data}")
                    return response_data
                else:
                    logger.warning(f"Tom API returned error {response.status}: {response_data}")
                    return {"success": False, "error": f"HTTP {response.status}", "detail": response_data}

        except Exception as e:
            logger.error(f"Tom instruction improvement failed: {e}")
            return {"success": False, "error": str(e)}

    async def suggest_next_actions(self, user_id: str, context: str) -> Dict:
        """Get personalized next action suggestions from Tom.

        Args:
            user_id: Unique identifier for the user
            context: Current conversation context including agent response

        Returns:
            API response dict containing suggestions or error info
        """
        try:
            url = f"{self.base_url}/suggest_next_actions"
            payload = {
                "user_id": user_id,
                "context": context
            }

            logger.debug(f"Calling Tom API for next action suggestions: {url}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

            async with self.session.post(url, json=payload) as response:
                response_data = await response.json()

                if response.status == 200:
                    logger.debug(f"Tom next action suggestions successful: {response_data}")
                    return response_data
                else:
                    logger.warning(f"Tom API returned error {response.status}: {response_data}")
                    return {"success": False, "error": f"HTTP {response.status}", "detail": response_data}

        except Exception as e:
            logger.error(f"Tom next action suggestions failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_conversation_status(self, user_id: str) -> Dict:
        """Get conversation status for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            API response dict containing conversation status
        """
        try:
            url = f"{self.base_url}/conversation_status"
            params = {"user_id": user_id}

            async with self.session.get(url, params=params) as response:
                response_data = await response.json()

                if response.status == 200:
                    return response_data
                else:
                    logger.warning(f"Tom API returned error {response.status}: {response_data}")
                    return {"success": False, "error": f"HTTP {response.status}", "detail": response_data}

        except Exception as e:
            logger.error(f"Tom conversation status failed: {e}")
            return {"success": False, "error": str(e)}