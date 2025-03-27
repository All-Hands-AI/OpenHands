# Microagents Overview

Microagents are specialized prompts that enhance OpenHands with domain-specific knowledge, repository-specific context
and task-specific workflows. They help by providing expert guidance, automating common tasks, and ensuring
consistent practices across projects.

## Microagent Categories

Currently OpenHands supports two categories of microagents:

- [Repository-specific Microagents](./microagents-repo): Repository-specific context and guidelines for OpenHands.
- [Public Microagents](./microagents-public): General guidelines triggered by keywords for all OpenHands users.

A microagent is classified as repository-specific or public depending on its location:

- Repository-specific microagents are located in a repository's `.openhands/microagents/` directory
- Public microagents are located in the official OpenHands repository inside the `/microagents` folder

When OpenHands works with a repository, it:

1. Loads **repository-specific** microagents from `.openhands/microagents/` if present in the repository.
2. Loads **public knowledge** microagents triggered by keywords in conversations
3. Loads **public tasks** microagents when explicitly requested by the user

You can check out the existing public microagents at the [official OpenHands repository](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/).

## Microagents Discovery and Loading

OpenHands uses the following process to discover and load microagents:

1. For **repository-specific** microagents:

   - Searches for `.openhands/microagents/repo.md` as the main repository instruction file
   - Recursively scans the `.openhands/microagents/knowledge/` directory for knowledge microagents
   - Recursively scans the `.openhands/microagents/tasks/` directory for task microagents
   - All `.md` files within these directories are processed, regardless of their depth

2. For **public** microagents:
   - Loads from the official OpenHands repository's `/microagents/knowledge/` and `/microagents/tasks/` directories
   - Only processes files that match their expected location patterns

Note that `README.md` files are automatically skipped during the loading process.

## Microagent Format

All microagents use markdown files with YAML frontmatter that have special instructions to help OpenHands activate them.

Check out the [syntax documentation](./microagents-syntax) for a comprehensive guide on how to configure your microagents.
