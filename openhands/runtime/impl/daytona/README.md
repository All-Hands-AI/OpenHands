# Daytona Runtime

[Daytona](https://www.daytona.io/) is a platform that provides a secure and elastic infrastructure for running AI-generated code. It provides all the necessary features for an AI Agent to interact with a codebase. It provides a Daytona SDK with official Python and TypeScript interfaces for interacting with Daytona, enabling you to programmatically manage development environments and execute code.

## Getting started

1. Sign in at https://app.daytona.io/

1. Generate and copy your API key

1. Set the following environment variables before running the OpenHands app on your local machine or via a `docker run` command:

```bash
    RUNTIME="daytona"
    DAYTONA_API_KEY="<your-api-key>"
```
Optionally, if you don't want your sandboxes to default to the US region, set:

```bash
    DAYTONA_TARGET="eu"
```

## Documentation
Read more by visiting our [documentation](https://www.daytona.io/docs/) page.
