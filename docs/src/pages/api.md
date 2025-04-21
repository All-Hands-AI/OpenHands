---
title: API Reference
description: OpenHands API Reference
---

# OpenHands API Reference

Welcome to the OpenHands API Reference. This documentation provides details about the available API endpoints, request parameters, and response formats.

## Interactive API Documentation

We provide an interactive API documentation using Swagger UI, which allows you to explore and test the API endpoints:

<div className="container">
  <div className="row">
    <div className="col col--6">
      <div className="card margin-bottom--lg">
        <div className="card__header">
          <h3>Swagger UI</h3>
        </div>
        <div className="card__body">
          <p>
            Interactive API documentation with Swagger UI. Explore and test API endpoints directly in your browser.
          </p>
        </div>
        <div className="card__footer">
          <a className="button button--primary button--block" href="/swagger-ui/">Open Swagger UI</a>
        </div>
      </div>
    </div>
    <div className="col col--6">
      <div className="card margin-bottom--lg">
        <div className="card__header">
          <h3>OpenAPI Specification</h3>
        </div>
        <div className="card__body">
          <p>
            Download the raw OpenAPI specification file for use with other tools like Postman.
          </p>
        </div>
        <div className="card__footer">
          <a className="button button--secondary button--block" href="/openapi.json">Download OpenAPI Spec</a>
        </div>
      </div>
    </div>
  </div>
</div>

## Base URLs

The API is available at the following base URLs:

- **Production**: `https://app.all-hands.dev`
- **Development**: `http://localhost:3000`

## Authentication

Authentication details will be provided in a future update.

## API Endpoints Overview

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

For a complete list of endpoints and detailed documentation, please use the [Swagger UI](/swagger-ui/) interface.