# GUI Mode

OpenHands provides a Graphical User Interface (GUI) mode for interacting with the AI assistant.

## Installation and Setup

1. Follow the instructions in the [Installation](../installation) guide to install OpenHands.
2. After running the command, access OpenHands at [http://localhost:3000](http://localhost:3000).

## Interacting with the GUI

### Initial Setup

1. Upon first launch, you'll see a settings page.
2. Select an `LLM Provider` and `LLM Model` from the dropdown menus. If the required model does not exist in the list,
   toggle `Advanced` options and enter it with the correct prefix in the `Custom Model` text box.
3. Enter the corresponding `API Key` for your chosen provider.
4. Click `Save Changes` to apply the settings.

### GitHub Token Setup

OpenHands automatically exports a `GITHUB_TOKEN` to the shell environment if it is available. This can happen in two ways:

- **Local Installation**: The user directly inputs their GitHub token.
<details>
  <summary>Setting Up a GitHub Token</summary>
  1. **Generate a Personal Access Token (PAT)**:
   - On GitHub, go to Settings > Developer Settings > Personal Access Tokens > Tokens (classic).
   - Click `Generate new token (classic)`.
   - Required scopes:
     - `repo` (Full control of private repositories)
  2. **Enter Token in OpenHands**:
   - Click the Settings button (gear icon).
   - Navigate to the `GitHub Settings` section.
   - Paste your token in the `GitHub Token` field.
   - Click `Save Changes` to apply the changes.
</details>

<details>
  <summary>Organizational Token Policies</summary>

  If you're working with organizational repositories, additional setup may be required:

  1. **Check Organization Requirements**:
   - Organization admins may enforce specific token policies.
   - Some organizations require tokens to be created with SSO enabled.
   - Review your organization's [token policy settings](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization).
  2. **Verify Organization Access**:
   - Go to your token settings on GitHub.
   - Look for the organization under `Organization access`.
   - If required, click `Enable SSO` next to your organization.
   - Complete the SSO authorization process.
</details>

<details>
  <summary>Troubleshooting</summary>

  Common issues and solutions:

  - **Token Not Recognized**:
     - Ensure the token is properly saved in settings.
     - Check that the token hasn't expired.
     - Verify the token has the required scopes.
     - Try regenerating the token.

  - **Organization Access Denied**:
     - Check if SSO is required but not enabled.
     - Verify organization membership.
     - Contact organization admin if token policies are blocking access.

  - **Verifying Token Works**:
     - The app will show a green checkmark if the token is valid.
     - Try accessing a repository to confirm permissions.
     - Check the browser console for any error messages.
</details>

- **OpenHands Cloud**: The token is obtained through GitHub OAuth authentication.

<details>
  <summary>OAuth Authentication</summary>

  When using OpenHands Cloud, the GitHub OAuth flow requests the following permissions:
   - Repository access (read/write)
   - Workflow management
   - Organization read access

  To authenticate OpenHands:
   - Click `Sign in with GitHub` when prompted.
   - Review the requested permissions.
   - Authorize OpenHands to access your GitHub account.
   - If using an organization, authorize organization access if prompted.
</details>

### Advanced Settings

1. Inside the Settings page, toggle `Advanced` options to access additional settings.
2. Use the `Custom Model` text box to manually enter a model if it's not in the list.
3. Specify a `Base URL` if required by your LLM provider.

### Interacting with the AI

1. Type your prompt in the input box.
2. Click the send button or press Enter to submit your message.
3. The AI will process your input and provide a response in the chat window.
4. You can continue the conversation by asking follow-up questions or providing additional information.

## Tips for Effective Use

- Be specific in your requests to get the most accurate and helpful responses, as described in the [prompting best practices](../prompting/prompting-best-practices).
- Use the workspace panel to explore your project structure.
- Use one of the recommended models, as described in the [LLMs section](usage/llms/llms.md).

Remember, the GUI mode of OpenHands is designed to make your interaction with the AI assistant as smooth and intuitive
as possible. Don't hesitate to explore its features to maximize your productivity.
