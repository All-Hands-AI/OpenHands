# Project Management Tool Integrations

## Overview

OpenHands Cloud integrates with project management platforms (Jira Cloud, Jira Data Center, and Linear) to enable AI-powered task delegation. Users can invoke the OpenHands agent by:
- Adding `@openhands` in ticket comments
- Adding the `openhands` label to tickets

## Prerequisites

Integration requires two levels of setup:
1. **Platform Configuration** - Administrative setup of service accounts and webhooks on your project management platform (see individual platform documentation below)
2. **Workspace Integration** - Self-service configuration through the OpenHands Cloud UI to link your OpenHands account to the target workspace

### Platform-Specific Setup Guides:
- [Linear Integration](./linear-integration.md)
- [Jira Cloud Integration](./jira-integration.md)
- [Jira Data Center Integration](./jira-dc-integration.md)

## Usage

Once both the platform configuration and workspace integration are completed, users can trigger the OpenHands agent within their project management platforms using two methods:

### Method 1: Comment Mention
Add a comment to any issue with `@openhands` followed by your task description:
```
@openhands Please implement the user authentication feature described in this ticket
```

### Method 2: Label-based Delegation
Add the label `openhands` to any issue. The OpenHands agent will automatically process the issue based on its description and requirements.

## What Happens Next

1. The webhook triggers when you mention `@openhands` or add the `openhands` label
2. OpenHands Cloud receives the event and processes the task
3. The OpenHands agent analyzes the issue and begins implementation
4. Progress updates and results are posted back to the original issue
5. You can follow the link from the agent's acknowledgment message to monitor live progress through the OpenHands Cloud UI

## Troubleshooting

### Platform Configuration Issues
- **Webhook not triggering**: Verify the webhook URL is correct and the proper event types are selected (Comment, Issue updated)
- **API authentication failing**: Check API key/token validity and ensure required scopes are granted
- **Permission errors**: Ensure the service account has access to relevant projects/teams and appropriate permissions

### Workspace Integration Issues
- **Workspace linking requests credentials**: If there are no active workspace integrations for the workspace you specified, you need to configure it first. Contact your platform administrator if you don't have the necessary access
- **OAuth flow fails**: Ensure you're signing in with the same Git provider account that contains the repositories you want OpenHands to work on
- **Integration not found**: Verify the workspace name matches exactly and that platform configuration was completed first

### General Issues
- **Agent not responding**: Check webhook logs in your platform settings and verify service account status
- **Authentication errors**: Verify Git provider permissions and OpenHands Cloud access
- **Partial functionality**: Ensure both platform configuration and workspace integration are properly completed

### Getting Help
For additional support, contact OpenHands Cloud support with:
- Your integration platform (Linear, Jira Cloud, or Jira Data Center)
- Workspace name
- Error logs from webhook/integration attempts
- Screenshots of configuration settings (without sensitive credentials)
