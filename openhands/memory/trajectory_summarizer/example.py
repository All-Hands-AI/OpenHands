"""
Example usage of the trajectory summarizer.
"""

import json
import os
from typing import Any, Dict

import aiofiles  # type: ignore

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM
from openhands.memory.trajectory_summarizer import (
    TrajectorySummarizer,
    load_from_huggingface,
    process_dataset_example,
)


def example_summarize_from_huggingface(
    dataset_name: str = 'all-hands/openhands-feedback',
    split: str = 'train',
    limit: int = 1,
    output_file: str = 'summary_example.json',
) -> Dict[str, Any]:
    """
    Example function to summarize trajectories from HuggingFace.

    Args:
        dataset_name: Name of the dataset on HuggingFace
        split: Dataset split to load
        limit: Maximum number of trajectories to process
        output_file: File to save the summary

    Returns:
        The summary dictionary
    """
    # Load dataset
    dataset = load_from_huggingface(dataset_name, split)

    # Take only the first example
    example = dataset[0] if len(dataset) > 0 else None
    if not example:
        raise ValueError('No examples found in the dataset')

    # Process the example
    processed_example = process_dataset_example(example)

    # Create LLM config
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key=os.environ.get('OPENAI_API_KEY'),
        api_base=os.environ.get('OPENAI_BASE_URL'),
    )

    # Create LLM
    llm = LLM(llm_config)

    # Initialize the summarizer
    summarizer = TrajectorySummarizer(
        llm=llm,
        temperature=0.0,
    )

    # Summarize the trajectory
    summary = summarizer.summarize_trajectory(processed_example['formatted_trajectory'])

    # Save the summary
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    return summary


def example_summarize_from_json(
    trajectory_file: str = 'trajectory.json',
    output_file: str = 'summary_example.json',
) -> Dict[str, Any]:
    """
    Example function to summarize a trajectory from a JSON file.

    Args:
        trajectory_file: Path to the trajectory JSON file
        output_file: File to save the summary

    Returns:
        The summary dictionary
    """
    # Load the trajectory
    with open(trajectory_file, 'r') as f:
        trajectory = json.load(f)

    # Create LLM config
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key=os.environ.get('OPENAI_API_KEY'),
        api_base=os.environ.get('OPENAI_BASE_URL'),
    )

    # Create LLM
    llm = LLM(llm_config)

    # Initialize the summarizer
    summarizer = TrajectorySummarizer(
        llm=llm,
        temperature=0.0,
    )

    # Summarize the trajectory
    summary = summarizer.summarize_trajectory(trajectory)

    # Save the summary
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    return summary


async def example_summarize_from_conversation(
    event_stream,
    output_file: str = 'summary_example.json',
) -> Dict[str, Any]:
    """
    Example function to summarize a conversation from its event stream.

    Args:
        event_stream: The event stream of the conversation
        output_file: File to save the summary

    Returns:
        The summary dictionary
    """
    # Create LLM config
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key=os.environ.get('OPENAI_API_KEY'),
        api_base=os.environ.get('OPENAI_BASE_URL'),
    )

    # Create LLM
    llm = LLM(llm_config)

    # Initialize the summarizer
    summarizer = TrajectorySummarizer(
        llm=llm,
        temperature=0.0,
    )

    # Summarize the conversation
    summary = await summarizer.summarize_conversation(event_stream)

    # Save the summary - use async file operations
    async with aiofiles.open(output_file, 'w') as f:
        await f.write(json.dumps(summary, indent=2))

    return summary


if __name__ == '__main__':
    # Example usage
    print('Summarizing from HuggingFace dataset...')
    summary = example_summarize_from_huggingface()

    print('\nSummary:')
    print(f"Overall summary: {summary['overall_summary']}")
    print(f"Number of segments: {len(summary['segments'])}")

    print('\nFirst segment:')
    if summary['segments']:
        segment = summary['segments'][0]
        print(f"Title: {segment['title']}")
        print(f"Timestamp range: {segment['timestamp_range']}")
        print(f"Summary: {segment['summary']}")
        if 'ids' in segment:
            print(f"IDs: {segment['ids']}")
