# GUI Mode

## Introduction

OpenHands provides a user-friendly Graphical User Interface (GUI) mode for interacting with the AI assistant. This mode offers an intuitive way to set up the environment, manage settings, and communicate with the AI.

## Installation and Setup

1. Follow the instructions in the [Installation](../installation) guide to install OpenHands.

2. After running the command, access OpenHands at [http://localhost:3000](http://localhost:3000).

## Interacting with the GUI

### Initial Setup

1. Upon first launch, you'll see a settings modal.
2. Select an `LLM Provider` and `LLM Model` from the dropdown menus.
3. Enter the corresponding `API Key` for your chosen provider.
4. Click "Save" to apply the settings.

### GitHub Token Setup

OpenHands automatically exports a `GITHUB_TOKEN` to the shell environment if it is available. This can happen in two ways:

1. **Locally (OSS)**: The user directly inputs their GitHub token
2. **Online (SaaS)**: The token is obtained through GitHub OAuth authentication

#### Setting Up a Local GitHub Token

1. **Generate a Personal Access Token (PAT)**:
   - Go to GitHub Settings > Developer Settings > Personal Access Tokens > Tokens (classic)
   - Click "Generate new token (classic)"
   - Required scopes:
     - `repo` (Full control of private repositories)
     - `workflow` (Update GitHub Action workflows)
     - `read:org` (Read organization data)

2. **Enter Token in OpenHands**:
   - Click the Settings button (gear icon) in the top right
   - Navigate to the "GitHub" section
   - Paste your token in the "GitHub Token" field
   - Click "Save" to apply the changes

#### Organizational Token Policies

If you're working with organizational repositories, additional setup may be required:

1. **Check Organization Requirements**:
   - Organization admins may enforce specific token policies
   - Some organizations require tokens to be created with SSO enabled
   - Review your organization's [token policy settings](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization)

2. **Verify Organization Access**:
   - Go to your token settings on GitHub
   - Look for the organization under "Organization access"
   - If required, click "Enable SSO" next to your organization
   - Complete the SSO authorization process

#### OAuth Authentication (Online Mode)

When using OpenHands in online mode, the GitHub OAuth flow:

1. Requests the following permissions:
   - Repository access (read/write)
   - Workflow management
   - Organization read access

2. Authentication steps:
   - Click "Sign in with GitHub" when prompted
   - Review the requested permissions
   - Authorize OpenHands to access your GitHub account
   - If using an organization, authorize organization access if prompted

#### Troubleshooting

Common issues and solutions:

1. **Token Not Recognized**:
   - Ensure the token is properly saved in settings
   - Check that the token hasn't expired
   - Verify the token has the required scopes
   - Try regenerating the token

2. **Organization Access Denied**:
   - Check if SSO is required but not enabled
   - Verify organization membership
   - Contact organization admin if token policies are blocking access

3. **Verifying Token Works**:
   - The app will show a green checkmark if the token is valid
   - Try accessing a repository to confirm permissions
   - Check the browser console for any error messages
   - Use the "Test Connection" button in settings if available

### Advanced Settings

1. Toggle `Advanced Options` to access additional settings.
2. Use the `Custom Model` text box to manually enter a model if it's not in the list.
3. Specify a `Base URL` if required by your LLM provider.

### Main Interface

The main interface consists of several key components:

1. **Chat Window**: The central area where you can view the conversation history with the AI assistant.
2. **Input Box**: Located at the bottom of the screen, use this to type your messages or commands to the AI.
3. **Send Button**: Click this to send your message to the AI.
4. **Settings Button**: A gear icon that opens the settings modal, allowing you to adjust your configuration at any time.
5. **Workspace Panel**: Displays the files and folders in your workspace, allowing you to navigate and view files, or the agent's past commands or web browsing history.

### Interacting with the AI

1. Type your question, request, or task description in the input box.
2. Click the send button or press Enter to submit your message.
3. The AI will process your input and provide a response in the chat window.
4. You can continue the conversation by asking follow-up questions or providing additional information.

## Tips for Effective Use

1. Be specific in your requests to get the most accurate and helpful responses, as described in the [prompting best practices](../prompting/prompting-best-practices).
2. Use the workspace panel to explore your project structure.
3. Use one of the recommended models, as described in the [LLMs section](usage/llms/llms.md).

Remember, the GUI mode of OpenHands is designed to make your interaction with the AI assistant as smooth and intuitive as possible. Don't hesitate to explore its features to maximize your productivity.
