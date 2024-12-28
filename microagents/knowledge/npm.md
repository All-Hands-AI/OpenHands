---
name: npm
version: 1.0.0
author: openhands
agent: CodeActAgent
category: development
trigger_type: keyword
triggers:
  - npm
  - node
tags:
  - npm
  - node
  - package-management
requires:
  - npm
  - yes
---

# NPM Package Management

## Overview
Provides guidance for npm package management in non-interactive environments.

## Important Notes
When using npm to install packages, you will not be able to use an interactive shell, and it may be hard to confirm your actions.
As an alternative, you can pipe in the output of the unix "yes" command to confirm your actions.

## Examples

### Non-interactive Package Installation
```bash
yes | npm install package-name
```

### Automated Package Updates
```bash
yes | npm update
```
