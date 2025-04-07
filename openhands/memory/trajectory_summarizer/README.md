# Trajectory Summarizer

This module provides functionality to summarize agent trajectories within OpenHands. It uses LLMs to generate structured summaries of interactions between users and the OpenHands agent.

## Features

- Load trajectories from HuggingFace datasets (e.g., all-hands/openhands-feedback)
- Process and clean trajectory data for summarization
- Generate structured summaries with overall summary and segments
- Parse and process timestamps for better organization
- Batch processing for multiple trajectories

## Usage

### Basic Usage

```python
from openhands.memory.trajectory_summarizer import TrajectorySummarizer

# Initialize the summarizer
summarizer = TrajectorySummarizer(
    api_key="your-openai-api-key",  # Optional, can use environment variable
    base_url="your-openai-base-url",  # Optional, can use environment variable
    model="gpt-4o",  # Default model
    temperature=0.0,  # Default temperature
)

# Summarize a trajectory
trajectory_data = [...]  # Your trajectory data as a list of dictionaries
summary = summarizer.summarize_trajectory(trajectory_data)

print(summary["overall_summary"])
for segment in summary["segments"]:
    print(f"Segment: {segment['title']}")
    print(f"Time: {segment['timestamp_range']}")
    print(f"Summary: {segment['summary']}")
```

### Loading from HuggingFace

```python
from openhands.memory.trajectory_summarizer import (
    load_from_huggingface,
    process_dataset_example,
    TrajectorySummarizer,
)

# Load dataset
dataset = load_from_huggingface("all-hands/openhands-feedback", "train")

# Process an example
example = dataset[0]
processed_example = process_dataset_example(example)

# Summarize
summarizer = TrajectorySummarizer()
summary = summarizer.summarize_trajectory(processed_example['formatted_trajectory'])
```

### Command-line Interface

The module also provides a command-line interface for batch processing:

```bash
python -m openhands.memory.trajectory_summarizer.cli \
    --dataset all-hands/openhands-feedback \
    --split train \
    --limit 10 \
    --output-dir ./summaries \
    --api-key your-openai-api-key \
    --base-url your-openai-base-url \
    --model gpt-4o
```

## Output Format

The summarizer generates a structured JSON output with the following format:

```json
{
  "overall_summary": "A concise summary of the entire interaction",
  "segments": [
    {
      "timestamp_range": "HH:MM:SS-HH:MM:SS",
      "title": "A short, descriptive title for this segment",
      "summary": "A detailed summary of what happened in this segment",
      "start_timestamp": "HH:MM:SS",
      "end_timestamp": "HH:MM:SS"
    },
    ...
  ]
}
```

## Requirements

- OpenAI API access (or compatible API)
- HuggingFace datasets library
- Python 3.8+
