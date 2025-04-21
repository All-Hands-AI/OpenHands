---
title: API Reference
description: OpenHands API Reference
---

# OpenHands API Reference

Welcome to the OpenHands API Reference. This documentation provides details about the available API endpoints, request parameters, and response formats.

## Base URLs

The API is available at the following base URLs:

- **Production**: `https://app.all-hands.dev`
- **Development**: `http://localhost:3000`

## Authentication

Authentication details will be provided in a future update.

## API Endpoints

The API provides various endpoints for interacting with OpenHands. Below are some of the key endpoints:

### Health Check

```
GET /health
```

Check if the API is running.

### Runtime Configuration

```
GET /api/conversations/{conversation_id}/config
```

Retrieve the runtime configuration (session ID and runtime ID).

### VSCode URL

```
GET /api/conversations/{conversation_id}/vscode-url
```

Get the VSCode URL for the conversation.

### Runtime Hosts

```
GET /api/conversations/{conversation_id}/web-hosts
```

Get the hosts used by the runtime.

### Submit Feedback

```
POST /api/conversations/{conversation_id}/submit-feedback
```

Submit user feedback for a conversation.

### List Files

```
GET /api/conversations/{conversation_id}/list-files
```

List files in the specified path.

### Get File Content

```
GET /api/conversations/{conversation_id}/select-file
```

Retrieve the content of a specified file.

### Download Workspace as Zip

```
GET /api/conversations/{conversation_id}/zip-directory
```

Download the current workspace as a zip file.

### Git Changes

```
GET /api/conversations/{conversation_id}/git/changes
```

Get git changes in the workspace.

### Git Diff

```
GET /api/conversations/{conversation_id}/git/diff
```

Get git diff for a specific file.

## OpenAPI Specification

The complete OpenAPI specification is available [here](/openapi.json).