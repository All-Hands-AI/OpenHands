---
name: Duplicate "Let me search" Messages
about: Web search responses show duplicate "Let me search for this information" messages
title: Duplicate "Let me search" messages during web search
labels: bug
assignees: ''

---

### Is there an existing issue for the same bug?

- [X] I have checked the existing issues.

### Describe the bug and reproduction steps

When performing a web search, the response "Let me search for this information." is displayed twice before the actual answer is received.

Steps to reproduce:
1. Start a new session
2. Enter the prompt: "What is the area in square miles of the state of California?"
3. Observe that the response "Let me search for this information." appears twice before the actual answer

### OpenHands Installation

Docker command in README

### OpenHands Version

0.15.0

### Operating System

MacOS

### Logs, Errors, Screenshots, and Additional Context

Both of the duplicate responses:
- Have the source of "agent"
- Have the same "thought"
- First response appears to initiate the search
- Second response appears when reading the resulting page

The issue likely occurs in frontend/src/services/actions.ts related to ActionType.BROWSE handling.

Screenshot showing the duplicate messages has been attached to the original report.