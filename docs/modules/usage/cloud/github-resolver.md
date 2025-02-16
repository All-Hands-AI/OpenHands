# Cloud GitHub Resolver

The GitHub Resolver is a powerful integration between Cloud OpenHands and GitHub that helps automate code fixes and provide intelligent assistance for your repositories.

## Setup and Prerequisites

### Automatic Availability
When you grant Cloud OpenHands access to a repository, the GitHub Resolver becomes immediately available for that repository. No additional setup is required for the resolver itself.

### User Configuration
Before using the resolver, users must:
1. Log in to Cloud OpenHands
2. Configure their LLM settings in their user profile

## Using the GitHub Resolver

The GitHub Resolver can be used in several ways to assist with your development workflow:

### 1. Issue Resolution
- Label any issue with `openhands` to request an automated fix attempt
- Cloud OpenHands will analyze the issue and attempt to create a solution

### 2. Pull Request Assistance
You can interact with OpenHands in pull requests using `@openhands` in top-level comments to:
- Ask questions about the PR without making any changes
- Request updates to the PR based on feedback
- Get code explanations or suggestions

### 3. Inline Code Comments
- Use `@openhands` in individual inline comments
- Same functionality as top-level comments but scoped to specific code sections
- Perfect for targeted questions or suggestions about specific parts of the code

### Privacy and Access Control
- Agent conversations are private to the initiating user
- Only the user who starts an OpenHands job will have access to the conversation and resolution attempt
- This ensures sensitive discussions and debugging sessions remain private

## Best Practices
- Use clear, specific descriptions in issues and comments to help OpenHands understand the context
- When requesting fixes, provide as much detail as possible about the expected behavior
- For inline comments, focus on specific code sections rather than broad changes