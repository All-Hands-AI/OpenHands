# OpenHands GitHub Webhook Listener

This container provides a webhook listener for GitHub events that triggers OpenHands automation processes.

## Features

- Accepts GitHub webhook events (PR opened, updated, reopened)
- Validates webhook signatures for security
- Triggers OpenHands automation for code review and analysis
- Creates conversations in OpenHands for each PR event

## Setup Instructions

### 1. Build and Deploy the Container

```bash
# Clone the repository
git clone https://github.com/srikanthkaranki/OpenHands.git
cd OpenHands

# Build and start the webhook container
cd containers/webhook
docker-compose up -d
```

### 2. Configure GitHub Webhook

1. Go to your GitHub repository
2. Navigate to Settings > Webhooks
3. Click "Add webhook"
4. Set the Payload URL to your server's URL: `https://your-server.com:8000/api/webhooks/github`
5. Set Content type to `application/json`
6. (Optional) Set a secret for added security
7. Select "Let me select individual events"
8. Check "Pull requests"
9. Click "Add webhook"

### 3. Configure Environment Variables

For security, set the webhook secret as an environment variable:

```bash
# Create a .env file
echo "GITHUB_WEBHOOK_SECRET=your_secret_here" > .env

# Restart the container to apply changes
docker-compose down
docker-compose up -d
```

## Testing the Webhook

1. Create a new PR in your GitHub repository
2. The webhook will receive the event and create a new conversation in OpenHands
3. OpenHands will process the PR and provide feedback

## Supported Events

Currently, the webhook supports the following GitHub events:

- `pull_request` with actions:
  - `opened`: When a new PR is created
  - `synchronize`: When a PR is updated with new commits
  - `reopened`: When a closed PR is reopened

## Customization

You can customize the automation behavior by modifying the webhook service:

- Edit `/openhands/integrations/github/webhook_service.py` to change how PRs are processed
- Add support for additional GitHub events by updating `/openhands/server/routes/webhooks.py`

## Troubleshooting

- Check the container logs: `docker-compose logs -f`
- Verify your webhook URL is accessible from GitHub
- Ensure the webhook secret matches between GitHub and your environment variables
- Check GitHub's webhook delivery logs for any errors