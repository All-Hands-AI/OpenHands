"""
Trajectory summarization module for OpenHands.

This module provides functionality to summarize agent trajectories.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from datasets import load_dataset

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.events.serialization.event import event_to_trajectory
from openhands.events.stream import EventStream
from openhands.llm.llm import LLM


def load_from_huggingface(
    dataset_name: str = 'all-hands/openhands-feedback', split: str = 'train'
):
    """
    Load trajectory data from the HuggingFace dataset.

    Args:
        dataset_name: Name of the dataset on HuggingFace
        split: Dataset split to load (default: "train")

    Returns:
        List of trajectories from the dataset
    """
    dataset = load_dataset(dataset_name, split=split)
    return dataset


def extract_timestamps(
    timestamp_range: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract start and end timestamps from a timestamp range string.

    Args:
        timestamp_range: String in format "HH:MM:SS-HH:MM:SS" or "HH:MM-HH:MM"

    Returns:
        Tuple of (start_timestamp, end_timestamp)
    """
    # Check if timestamp_range is valid
    if not timestamp_range or not isinstance(timestamp_range, str):
        return None, None

    # Split by hyphen to get start and end
    parts = timestamp_range.split('-')
    if len(parts) != 2:
        return None, None

    start_time = parts[0].strip()
    end_time = parts[1].strip()

    return start_time, end_time


def parse_llm_response_to_json(llm_response: str) -> Dict[str, Any]:
    """
    Parse the LLM response into a JSON object.

    Args:
        llm_response: The raw text response from the LLM

    Returns:
        A dictionary parsed from the JSON in the response
    """
    # Clean up the response to extract just the JSON part
    # Remove any markdown code block indicators
    cleaned_response = re.sub(r'```json|```', '', llm_response).strip()

    try:
        # Try direct JSON parsing
        parsed_data = json.loads(cleaned_response)

        # Process timestamps for each segment
        if 'segments' in parsed_data and isinstance(parsed_data['segments'], list):
            for segment in parsed_data['segments']:
                if 'timestamp_range' in segment:
                    # Extract start and end timestamps
                    start_time, end_time = extract_timestamps(
                        segment['timestamp_range']
                    )

                    # Add them to the segment
                    segment['start_timestamp'] = start_time
                    segment['end_timestamp'] = end_time

                # Ensure ids field exists (new format)
                if 'ids' not in segment:
                    segment['ids'] = []
                
                # Ensure ids are integers
                if 'ids' in segment and isinstance(segment['ids'], list):
                    # Convert string IDs to integers if possible
                    processed_ids = []
                    for id_value in segment['ids']:
                        try:
                            if isinstance(id_value, str) and id_value.isdigit():
                                processed_ids.append(int(id_value))
                            else:
                                processed_ids.append(id_value)
                        except (ValueError, TypeError):
                            # Keep original value if conversion fails
                            processed_ids.append(id_value)
                    
                    segment['ids'] = processed_ids

        return parsed_data
    except json.JSONDecodeError as e:
        logger.error(f'JSON parsing error: {e}')
        # If parsing fails, return a minimal valid structure
        return {'overall_summary': 'Failed to parse response', 'segments': []}


class TrajectoryProcessor:
    """
    Process and prepare trajectory data for summarization.
    """

    @staticmethod
    def preprocess_trajectory(
        trajectory_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Preprocess a raw trajectory data to extract only useful fields for summarization.

        Args:
            trajectory_data: The raw trajectory data as a list of dictionaries

        Returns:
            A simplified list of dictionaries with only relevant fields
        """
        processed_data = []

        for item in trajectory_data:
            # Extract relevant information - always include id and source even for empty content
            # This ensures all messages are represented in the trajectory
            processed_item = {
                'action': item.get('action', ''),
                'id': item.get('id'),
                'source': item.get('source', ''),
            }

            # Skip completely empty items without any identifiable information
            if not processed_item['id'] and not processed_item.get('timestamp'):
                continue

            # Add content if available
            if (
                item.get('content')
                and isinstance(item['content'], str)
                and item['content'].strip()
            ):
                processed_item['content'] = item['content']

            # Add message if available and different from content
            if (
                item.get('message')
                and isinstance(item['message'], str)
                and item['message'].strip()
            ):
                # Only add message if it's different from content or content is not present
                if not item.get('content') or item['message'] != item['content']:
                    processed_item['message'] = item['message']

            # Add observation if available
            if (
                item.get('observation')
                and isinstance(item['observation'], str)
                and item['observation'].strip()
            ):
                processed_item['observation'] = item['observation']

            # Format timestamp if available
            if item.get('timestamp'):
                try:
                    if isinstance(item['timestamp'], datetime):
                        processed_item['timestamp'] = item['timestamp'].strftime(
                            '%Y-%m-%d %H:%M:%S'
                        )
                    else:
                        processed_item['timestamp'] = str(item['timestamp'])
                except Exception as e:
                    logger.error(f'Error formatting timestamp: {e}')

            processed_data.append(processed_item)

        return processed_data

    @staticmethod
    def format_trajectory_for_prompt(trajectory_data: List[Dict[str, Any]]) -> str:
        """
        Format the preprocessed trajectory data as a JSON string for the prompt.

        Args:
            trajectory_data: The preprocessed trajectory data

        Returns:
            A formatted JSON string
        """
        return json.dumps(trajectory_data, indent=2)


def process_dataset_example(example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a specific example from the HuggingFace dataset.

    Args:
        example: A dictionary representing one example from the dataset

    Returns:
        A processed trajectory ready for summarization
    """
    # Extract the trajectory from the example
    trajectory = example.get('trajectory', [])

    # Preprocess the trajectory
    processed_trajectory = TrajectoryProcessor.preprocess_trajectory(trajectory)

    # Format the trajectory for the prompt
    formatted_trajectory = TrajectoryProcessor.format_trajectory_for_prompt(
        processed_trajectory
    )

    return {
        'raw_trajectory': trajectory,
        'processed_trajectory': processed_trajectory,
        'formatted_trajectory': formatted_trajectory,
        'feedback': example.get('feedback', ''),
        'version': example.get('version', ''),
        'permissions': example.get('permissions', ''),
        'timestamp': example.get('timestamp', ''),
    }


class TrajectorySummarizer:
    """
    Summarize agent trajectories using LLM.
    """

    def __init__(
        self,
        llm: Optional[LLM] = None,
        llm_config: Optional[LLMConfig] = None,
        temperature: float = 0.0,
    ):
        """
        Initialize the trajectory summarizer.

        Args:
            llm: LLM instance to use for summarization
            llm_config: LLM configuration to use if llm is not provided
            temperature: Temperature for the model
        """
        self.llm = llm
        self.llm_config = llm_config
        self.temperature = temperature

        # Load the prompt template
        module_dir = Path(__file__).parent
        prompt_template_path = module_dir / 'LLM_one_shot_instruction.txt'
        with open(prompt_template_path, 'r') as f:
            self.prompt_template = f.read()

    def summarize_trajectory(
        self, trajectory: Union[str, List[Dict[str, Any]]], llm: Optional[LLM] = None
    ) -> Dict[str, Any]:
        """
        Summarize a trajectory using LLM.

        Args:
            trajectory: The trajectory data as a JSON string or list of dictionaries
            llm: Optional LLM instance to use for this specific summarization

        Returns:
            A dictionary containing the summarization
        """
        # If trajectory is a list, convert it to a JSON string
        if isinstance(trajectory, list):
            trajectory = TrajectoryProcessor.format_trajectory_for_prompt(
                TrajectoryProcessor.preprocess_trajectory(trajectory)
            )

        # Insert the formatted trajectory into the prompt
        prompt = self.prompt_template.replace('[TRAJECTORY_DATA]', trajectory)

        # Use the provided LLM, the instance LLM, or create a new one from config
        current_llm = llm or self.llm
        if current_llm is None:
            if self.llm_config is None:
                raise ValueError('Either llm or llm_config must be provided')
            current_llm = LLM(self.llm_config)

        # Create a message for the LLM
        message = {'role': 'user', 'content': prompt}

        # Call the LLM
        response = current_llm.completion(
            messages=[message],
            temperature=self.temperature,
        )

        # Extract the response text
        response_text = response.choices[0].message.content

        # Parse the response
        parsed_response = parse_llm_response_to_json(response_text)
        
        # Post-process to ensure all IDs between min and max are included in each segment
        if 'segments' in parsed_response and isinstance(parsed_response['segments'], list):
            for segment in parsed_response['segments']:
                if 'ids' in segment and isinstance(segment['ids'], list) and len(segment['ids']) > 1:
                    # Get numeric IDs only
                    numeric_ids = [id_val for id_val in segment['ids'] 
                                  if isinstance(id_val, (int, float)) or 
                                  (isinstance(id_val, str) and id_val.isdigit())]
                    
                    if numeric_ids:
                        # Convert string IDs to integers
                        numeric_ids = [int(id_val) if isinstance(id_val, str) else id_val 
                                      for id_val in numeric_ids]
                        
                        # Find min and max IDs
                        min_id = min(numeric_ids)
                        max_id = max(numeric_ids)
                        
                        # Create a complete range of IDs
                        complete_range = list(range(min_id, max_id + 1))
                        
                        # Add any missing IDs to the segment
                        for id_val in complete_range:
                            if id_val not in numeric_ids:
                                segment['ids'].append(id_val)
                        
                        # Sort the IDs for clarity
                        segment['ids'].sort()
        
        return parsed_response

    def batch_summarize_trajectories(
        self,
        trajectories: List[Union[str, List[Dict[str, Any]]]],
        llm: Optional[LLM] = None,
    ) -> List[Dict[str, Any]]:
        """
        Summarize multiple trajectories.

        Args:
            trajectories: List of trajectories to summarize
            llm: Optional LLM instance to use for all summarizations

        Returns:
            List of summarizations
        """
        results = []

        for trajectory in trajectories:
            try:
                summary = self.summarize_trajectory(trajectory, llm=llm)
                results.append(summary)
            except Exception as e:
                logger.error(f'Error summarizing trajectory: {e}')
                results.append({'overall_summary': f'Error: {str(e)}', 'segments': []})

        return results

    @staticmethod
    async def get_trajectory_from_event_stream(
        event_stream: EventStream, filter_hidden: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get the current trajectory from an event stream.

        Args:
            event_stream: The event stream to get the trajectory from
            filter_hidden: Whether to filter out hidden events

        Returns:
            The trajectory as a list of dictionaries
        """
        async_store = AsyncEventStoreWrapper(event_stream, filter_hidden=filter_hidden)
        trajectory = []

        async for event in async_store:
            trajectory.append(event_to_trajectory(event))

        return trajectory

    async def summarize_conversation(
        self,
        event_stream: EventStream,
        llm: Optional[LLM] = None,
        filter_hidden: bool = True,
    ) -> Dict[str, Any]:
        """
        Summarize a conversation from its event stream.

        Args:
            event_stream: The event stream of the conversation
            llm: Optional LLM instance to use for summarization
            filter_hidden: Whether to filter out hidden events

        Returns:
            A dictionary containing the summarization
        """
        # Get the trajectory from the event stream
        trajectory = await self.get_trajectory_from_event_stream(
            event_stream, filter_hidden=filter_hidden
        )
        
        # Debug: Print the trajectory
        logger.info(f"DEBUG - Raw Trajectory: {json.dumps(trajectory, indent=2)}")
        
        # Preprocess the trajectory
        processed_trajectory = TrajectoryProcessor.preprocess_trajectory(trajectory)
        logger.info(f"DEBUG - Processed Trajectory: {json.dumps(processed_trajectory, indent=2)}")

        # Summarize the trajectory
        summary = self.summarize_trajectory(trajectory, llm=llm)
        
        # Debug: Print the summary
        logger.info(f"DEBUG - Summary Result: {json.dumps(summary, indent=2)}")
        
        return summary
