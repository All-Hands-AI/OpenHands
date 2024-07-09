# Moatless Search Agent

This folder implements the Moatless-inspired agent specialized in code search tasks. The agent is based on the [moatless-tools](https://github.com/aorwall/moatless-tools) search loop.

# Usage

TODO: Add usage instructions

> Note: This agent only supports following languages: `python`, `java`, `typescript`, `javascript`.

# How it works

## Indexing

- Each file in the local repository corresponds to a [`CodeFile`](./repository.py#L27) object inside a [`FileRepository`](./repository.py#L224).
