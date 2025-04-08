"""LLM Critic module for selecting the best response from multiple candidates."""

import copy
import json
import requests
from typing import Any, Dict, List, Optional, Tuple

from litellm.types.utils import ModelResponse
from pydantic import SecretStr

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.retry_mixin import RetryMixin

# Special token IDs used by the critic model
ASSISTANT_PREFIX_TOKEN_IDS = [151644, 77091]
SPECIAL_IM_END_TOKEN_ID_FOR_RM = 151645


class LLMCritic(RetryMixin):
    """LLM Critic class for selecting the best response from multiple candidates."""

    def __init__(self, config: LLMConfig):
        """Initialize the LLM Critic.
        
        Args:
            config: The LLM configuration.
        """
        self.config = config
        self.model = config.critic_model or config.model
        self.api_key = config.critic_api_key or config.api_key
        self.base_url = config.critic_base_url or config.base_url
        
        # Validate configuration
        if not self.base_url:
            raise ValueError("Critic base_url is required")

    def get_token_reward(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get token-level rewards for a list of messages.
        
        Args:
            messages: List of messages to evaluate.
            
        Returns:
            Dictionary containing token IDs and their corresponding rewards.
        """
        data = {
            "model": self.model,
            "messages": messages
        }
        headers = {
            "Authorization": f"Bearer {self.api_key.get_secret_value() if self.api_key else ''}"
        }
        
        @self.retry_decorator(
            num_retries=self.config.num_retries,
            retry_exceptions=(
                requests.RequestException,
                requests.HTTPError,
                requests.Timeout,
                requests.JSONDecodeError
            ),
            retry_min_wait=self.config.retry_min_wait,
            retry_max_wait=self.config.retry_max_wait,
            retry_multiplier=self.config.retry_multiplier,
        )
        def _post_with_retry():
            response = requests.post(
                f"{self.base_url}/pooling",
                headers=headers,
                json=data,
                timeout=300
            )  # 5-minute timeout
            response.raise_for_status()  # Raise exception for non-200 status codes
            return response.json()
        
        response_data = _post_with_retry()
        token_level_rewards = response_data['data'][0]['data']
        token_ids = response_data['data'][0]['prompt_token_ids']
        assert len(token_level_rewards) == len(token_ids), f"token_level_rewards: {len(token_level_rewards)}, token_ids: {len(token_ids)}"
        return {
            "rewards": token_level_rewards,
            "token_ids": token_ids
        }

    def get_assistant_chunks_with_rewards(
        self, 
        token_ids: List[int], 
        token_rewards: List[float]
    ) -> Dict[str, Any]:
        """Split token IDs into chunks by identifying assistant message boundaries
        and extract the corresponding reward values.
        
        Args:
            token_ids: List of token IDs
            token_rewards: List of reward values corresponding to token IDs
            
        Returns:
            Dictionary with chunks, end token rewards, and end token positions
        """
        assert len(token_ids) == len(token_rewards), f"token_ids: {len(token_ids)}, token_rewards: {len(token_rewards)}"
        assistant_chunks = []
        end_token_rewards = []
        end_token_positions = []
        current_chunk = []
        in_assistant_message = False
        
        prefix_len = len(ASSISTANT_PREFIX_TOKEN_IDS)
        
        i = 0
        while i < len(token_ids):
            # Check if we have an assistant prefix pattern
            if (i <= len(token_ids) - prefix_len and 
                token_ids[i:i+prefix_len] == ASSISTANT_PREFIX_TOKEN_IDS):
                
                # If we were already in an assistant message, save the previous chunk
                if in_assistant_message and current_chunk:
                    assistant_chunks.append(current_chunk)
                    current_chunk = []
                
                # Start a new assistant chunk, including the prefix tokens
                current_chunk = token_ids[i:i+prefix_len]
                in_assistant_message = True
                i += prefix_len
            
            # Check for special RM token that might end a message
            elif token_ids[i] == SPECIAL_IM_END_TOKEN_ID_FOR_RM and in_assistant_message:
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
            'end_token_positions': end_token_positions
        }

    def score_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score a list of messages and return the rewards.
        
        Args:
            messages: List of messages to evaluate.
            
        Returns:
            Dictionary containing scores and analysis information.
        """
        # Get the token IDs and rewards
        result = self.get_token_reward(messages)
        token_ids = result['token_ids']
        token_rewards = result['rewards']

        # Get assistant chunks and end token rewards
        analysis = self.get_assistant_chunks_with_rewards(token_ids, token_rewards)

        # Verify this matches the expected count
        expected_count = len([m for m in messages if m['role'] == 'assistant'])
        logger.debug(f"Expected/Actual count: {expected_count}/{len(analysis['chunks'])}; Rewards: {analysis['end_token_rewards']}")
        
        return {
            "assistant_rewards": analysis['end_token_rewards'],
            "assistant_chunks": analysis['chunks'],
            "end_token_positions": analysis['end_token_positions'],
            "token_ids": token_ids,
            "token_rewards": token_rewards,
            "expected_count": expected_count,
            "actual_count": len(analysis['chunks'])
        }

    def evaluate_candidates(
        self, 
        messages: List[Dict[str, Any]], 
        candidate_responses: List[ModelResponse]
    ) -> Tuple[ModelResponse, Dict[str, Any]]:
        """Evaluate multiple candidate responses and select the best one.
        
        Args:
            messages: The conversation history.
            candidate_responses: List of candidate responses to evaluate.
            
        Returns:
            Tuple of (best response, evaluation results)
        """
        # Create a copy of messages for each candidate
        candidate_messages_list = []
        
        for response in candidate_responses:
            # Create a copy of the messages
            candidate_messages = copy.deepcopy(messages)
            
            # Add the candidate response as an assistant message
            if len(response['choices']) > 0:
                content = response['choices'][0]['message'].get('content', '')
                tool_calls = response['choices'][0]['message'].get('tool_calls', [])
                
                assistant_message = {
                    "role": "assistant",
                    "content": content
                }
                
                # Add tool calls if present
                if tool_calls:
                    assistant_message["tool_calls"] = tool_calls
                
                candidate_messages.append(assistant_message)
                candidate_messages_list.append(candidate_messages)
        
        # Score each candidate
        scores = []
        for candidate_msgs in candidate_messages_list:
            try:
                score_result = self.score_messages(candidate_msgs)
                # Get the last assistant reward (the one for the candidate response)
                if score_result["assistant_rewards"]:
                    scores.append(score_result["assistant_rewards"][-1])
                else:
                    scores.append(0.0)  # Default score if no rewards
            except Exception as e:
                logger.error(f"Error scoring candidate: {e}")
                scores.append(0.0)  # Default score on error
        
        # Find the best candidate
        if not scores:
            # If no scores, return the first candidate
            best_index = 0
        else:
            best_index = scores.index(max(scores))
        
        # Return the best candidate and the evaluation results
        evaluation_results = {
            "scores": scores,
            "best_index": best_index,
            "best_score": scores[best_index] if scores else 0.0,
            "num_candidates": len(candidate_responses)
        }
        
        return candidate_responses[best_index], evaluation_results