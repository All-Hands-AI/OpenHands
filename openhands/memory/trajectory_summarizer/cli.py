"""
Command-line interface for trajectory summarization.
"""

import argparse
import json
import os
from typing import List, Optional

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.memory.trajectory_summarizer.summarizer import (
    TrajectorySummarizer,
    load_from_huggingface,
    process_dataset_example,
)


def save_summaries(
    summaries: List[dict], output_dir: str, prefix: str = 'summary'
) -> None:
    """
    Save summaries to JSON files.

    Args:
        summaries: List of summary dictionaries
        output_dir: Directory to save the summaries
        prefix: Prefix for the summary filenames
    """
    os.makedirs(output_dir, exist_ok=True)

    for i, summary in enumerate(summaries):
        output_path = os.path.join(output_dir, f'{prefix}_{i}.json')
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f'Saved summary to {output_path}')


def main(
    dataset_name: str = 'all-hands/openhands-feedback',
    split: str = 'train',
    limit: Optional[int] = None,
    output_dir: str = './summaries',
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: str = 'gpt-4o',
) -> None:
    """
    Main function to run the trajectory summarizer.

    Args:
        dataset_name: Name of the dataset on HuggingFace
        split: Dataset split to load
        limit: Maximum number of trajectories to process
        output_dir: Directory to save the summaries
        api_key: OpenAI API key (for backward compatibility)
        base_url: Base URL for the OpenAI API (for backward compatibility)
        model: Model to use for summarization
    """
    logger.info(f'Loading dataset {dataset_name} (split: {split})')
    dataset = load_from_huggingface(dataset_name, split)

    # Limit the number of examples if specified
    if limit is not None and limit > 0:
        dataset = dataset.select(range(min(limit, len(dataset))))

    logger.info(f'Processing {len(dataset)} trajectories')

    processed_trajectories = []
    for i, record in enumerate(dataset):
        logger.info(f'Processing trajectory {i+1}/{len(dataset)}')
        processed_example = process_dataset_example(record)
        processed_trajectories.append(processed_example['formatted_trajectory'])

    # Create LLM config
    llm_config = LLMConfig(
        model=model,
        api_key=api_key,
        api_base=base_url,
    )

    # Create LLM
    llm = LLM(llm_config)

    # Initialize the summarizer
    summarizer = TrajectorySummarizer(
        llm=llm,
        temperature=0.0,
    )

    # Summarize the trajectories
    logger.info('Summarizing trajectories')
    summaries = summarizer.batch_summarize_trajectories(processed_trajectories)

    # Save the summaries
    logger.info(f'Saving summaries to {output_dir}')
    save_summaries(summaries, output_dir)

    logger.info('Done!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Summarize agent trajectories')
    parser.add_argument(
        '--dataset',
        type=str,
        default='all-hands/openhands-feedback',
        help='HuggingFace dataset name',
    )
    parser.add_argument('--split', type=str, default='train', help='Dataset split')
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of trajectories to process',
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./summaries',
        help='Directory to save summaries',
    )
    parser.add_argument('--api-key', type=str, default=None, help='OpenAI API key')
    parser.add_argument(
        '--base-url', type=str, default=None, help='Base URL for OpenAI API'
    )
    parser.add_argument(
        '--model', type=str, default='gpt-4o', help='Model to use for summarization'
    )

    args = parser.parse_args()

    main(
        dataset_name=args.dataset,
        split=args.split,
        limit=args.limit,
        output_dir=args.output_dir,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
    )
