"""LLM Critic module for selecting the best response from multiple candidates."""

import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

import requests
from litellm.types.utils import ModelResponse
from pydantic import BaseModel

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.fn_call_converter import (
    convert_fncall_messages_to_non_fncall_messages,
)
from openhands.llm.llm import LiteLLMMessage
from openhands.llm.retry_mixin import RetryMixin

# Special token IDs used by the critic model
ASSISTANT_PREFIX_TOKEN_IDS = [151644, 77091]
SPECIAL_IM_END_TOKEN_ID_FOR_RM = 151645


class ModelResponseWithCriticScore(ModelResponse):
    """Model response with critic score."""

    critic_score: float


class LLMCriticOutput(BaseModel):
    """Output of the LLM Critic."""

    assistant_rewards: list[float]
    token_ids: list[int]
    token_rewards: list[float]

    @property
    def last_reward(self) -> float:
        """Get the last reward."""
        assert len(self.assistant_rewards) > 0, 'No assistant rewards found'
        return self.assistant_rewards[-1]


class LLMCritic(RetryMixin):
    """LLM Critic class for selecting the best response from multiple candidates."""

    def __init__(self, config: LLMConfig):
        """Initialize the LLM Critic.

        Args:
            config: The LLM configuration.
        """
        self.config = config
        self.model = config.critic_model
        self.api_key = config.critic_api_key
        self.base_url = config.critic_base_url
        assert self.base_url, 'Critic base_url is required'
        assert self.api_key, 'Critic api_key is required'
        assert self.model, 'Critic model is required'

        # Validate configuration
        if not self.base_url:
            raise ValueError('Critic base_url is required')

    def _get_token_reward(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Get token-level rewards for a list of messages.

        Args:
            messages: List of messages to evaluate.

        Returns:
            Dictionary containing token IDs and their corresponding rewards.
        """
        data = {'model': self.model, 'messages': messages}
        headers = {
            'Authorization': f'Bearer {self.api_key.get_secret_value() if self.api_key else ""}'
        }

        @self.retry_decorator(
            num_retries=5,
            retry_exceptions=(
                requests.RequestException,
                requests.HTTPError,
                requests.Timeout,
                requests.JSONDecodeError,
            ),
            retry_min_wait=1,
            retry_max_wait=30,
            retry_multiplier=1,
        )
        def _post_with_retry():
            response = requests.post(
                f'{self.base_url}/pooling', headers=headers, json=data, timeout=300
            )  # 5-minute timeout
            response.raise_for_status()  # Raise exception for non-200 status codes
            return response.json()

        response_data = _post_with_retry()
        token_level_rewards = response_data['data'][0]['data']
        token_ids = response_data['data'][0]['prompt_token_ids']
        assert len(token_level_rewards) == len(token_ids), (
            f'token_level_rewards: {len(token_level_rewards)}, token_ids: {len(token_ids)}'
        )
        return {'rewards': token_level_rewards, 'token_ids': token_ids}

    def _get_assistant_chunks_with_rewards(
        self, token_ids: list[int], token_rewards: list[float]
    ) -> dict[str, Any]:
        """Split token IDs into chunks by identifying assistant message boundaries
        and extract the corresponding reward values.

        Args:
            token_ids: List of token IDs
            token_rewards: List of reward values corresponding to token IDs

        Returns:
            Dictionary with chunks, end token rewards, and end token positions
        """
        assert len(token_ids) == len(token_rewards), (
            f'token_ids: {len(token_ids)}, token_rewards: {len(token_rewards)}'
        )
        assistant_chunks: list[list[int]] = []
        end_token_rewards: list[float] = []
        end_token_positions: list[int] = []
        current_chunk: list[int] = []
        in_assistant_message = False

        prefix_len = len(ASSISTANT_PREFIX_TOKEN_IDS)

        i = 0
        while i < len(token_ids):
            # Check if we have an assistant prefix pattern
            if (
                i <= len(token_ids) - prefix_len
                and token_ids[i : i + prefix_len] == ASSISTANT_PREFIX_TOKEN_IDS
            ):
                # If we were already in an assistant message, save the previous chunk
                if in_assistant_message and current_chunk:
                    assistant_chunks.append(current_chunk)
                    current_chunk = []

                # Start a new assistant chunk, including the prefix tokens
                current_chunk = token_ids[i : i + prefix_len]
                in_assistant_message = True
                i += prefix_len

            # Check for special RM token that might end a message
            elif (
                token_ids[i] == SPECIAL_IM_END_TOKEN_ID_FOR_RM and in_assistant_message
            ):
                # Include the special token in the chunk
                current_chunk.append(token_ids[i])

                # Store the reward for this end token
                end_token_rewards.append(token_rewards[i])
                end_token_positions.append(i)

                # Save the completed chunk
                assistant_chunks.append(current_chunk)
                current_chunk = []
                in_assistant_message = False
                i += 1

            # Add to current chunk if we're in an assistant message
            elif in_assistant_message:
                current_chunk.append(token_ids[i])
                i += 1

            # Skip tokens not part of assistant messages
            else:
                i += 1

        # Add the last chunk if we have one
        if in_assistant_message and current_chunk:
            assistant_chunks.append(current_chunk)

        return {
            'chunks': assistant_chunks,
            'end_token_rewards': end_token_rewards,
            'end_token_positions': end_token_positions,
        }

    def score_messages(self, messages: list[dict[str, Any]]) -> LLMCriticOutput:
        """Score a list of messages and return the rewards.

        Args:
            messages: List of messages to evaluate.

        Returns:
            Dictionary containing scores and analysis information.
        """
        # Get the token IDs and rewards
        result = self._get_token_reward(messages)
        token_ids = result['token_ids']
        token_rewards = result['rewards']

        # Get assistant chunks and end token rewards
        analysis = self._get_assistant_chunks_with_rewards(token_ids, token_rewards)

        # Verify this matches the expected count
        expected_count = len([m for m in messages if m['role'] == 'assistant'])
        logger.debug(
            f'Expected/Actual count: {expected_count}/{len(analysis["chunks"])}; Rewards: {analysis["end_token_rewards"]}'
        )
        # Check if the number of detected assistant messages matches expectations
        if len(analysis['chunks']) != expected_count:
            logger.warning(
                f'Mismatch in expected ({expected_count}) '
                f'and actual ({len(analysis["chunks"])}) assistant messages during critic scoring. '
                'Please check the critic model and configuration.'
            )

        return LLMCriticOutput(
            assistant_rewards=analysis['end_token_rewards'],
            token_ids=token_ids,
            token_rewards=token_rewards,
        )

    def _check_prefix_messages(
        self, list_of_messages: list[list[dict[str, Any]]]
    ) -> None:
        """Check if the messages have the SAME prefix and the last message is an assistant message.

        Args:
            list_of_messages: List of messages to evaluate.

        Raises:
            ValueError: If the messages do not have the SAME prefix or the last message is not an assistant message.
        """
        assert len(list_of_messages) > 0, 'List of messages must be non-empty'
        prefix_messages = list_of_messages[0][:-1]
        for messages in list_of_messages:
            if messages[-1]['role'] != 'assistant':
                raise ValueError('Last message must be an assistant message')
            if messages[:-1] != prefix_messages:
                raise ValueError('Messages must have the same prefix')

    def evaluate_candidates(
        self, list_of_messages: list[list[dict[str, Any]]]
    ) -> list[tuple[int, LLMCriticOutput]]:
        """Evaluate multiple candidate responses and select the best one using threads.

        Args:
            list_of_messages: A list where each element is a conversation history.
                              Assume the SAME prefix, except for the last assistant message.

        Returns:
            List of tuples of [candidate_index, score]. The list might not include
            all indices if scoring failed for some candidates.
        """
        self._check_prefix_messages(list_of_messages)

        results: list[tuple[int, LLMCriticOutput]] = []
        futures: dict[Future, int] = {}
        start_time = time.time()

        # Use a ThreadPoolExecutor to run scoring in parallel
        # You might want to adjust max_workers based on your environment
        with ThreadPoolExecutor(
            max_workers=self.config.critic_num_candidates
        ) as executor:
            for i, messages in enumerate(list_of_messages):
                # Submit each candidate message list to the executor for scoring
                future = executor.submit(self.score_messages, messages)
                futures[future] = i  # Store the original index with the future

            for future in futures:
                original_index = futures[future]
                try:
                    # Get the result from the completed future
                    score_result: LLMCriticOutput = future.result()
                    results.append((original_index, score_result))
                except Exception as e:
                    # Log any exceptions that occurred during scoring for a specific candidate
                    logger.error(
                        f'Error scoring candidate {original_index}: {e}', exc_info=True
                    )

        # Sort results by original index to maintain order if needed, though not strictly required by return type
        results.sort(key=lambda x: x[0])
        logger.debug(f'LLM: critic scoring took {time.time() - start_time} seconds')
        return results


def convert_fncall_messages_and_candidate_responses_for_critic(
    prefix_messages: list[dict[str, Any]],
    candidate_response_messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    """Convert messages and candidate responses for critic scoring.

    Args:
        prefix_messages: List of prefix messages.
        candidate_response_messages: List of candidate response messages.
        tools: List of tools.

    Returns:
        List of converted messages.
    """
    converted_messages = []
    for response_message in candidate_response_messages:
        non_fn_call_messages_with_response = (
            convert_fncall_messages_to_non_fncall_messages(
                prefix_messages + [response_message], tools
            )
        )
        non_fn_call_response_message = non_fn_call_messages_with_response[-1]
        if not isinstance(non_fn_call_response_message, LiteLLMMessage):
            non_fn_call_response_message = LiteLLMMessage(
                **non_fn_call_response_message
            )
        converted_messages.append(non_fn_call_messages_with_response)
    return converted_messages
