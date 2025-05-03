# Trajectory Summarizer

This module provides functionality to summarize agent trajectories within OpenHands. It uses LLMs to generate structured summaries of interactions between users and the OpenHands agent.

## Features

- Load trajectories from HuggingFace datasets (e.g., all-hands/openhands-feedback)
- Process and clean trajectory data for summarization
- Generate structured summaries with overall summary and segments
- Parse and process timestamps for better organization
- Batch processing for multiple trajectories
