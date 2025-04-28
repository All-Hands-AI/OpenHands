# OpenHands Cloud API

OpenHands Cloud provides a REST API that allows you to programmatically interact with the service. This is useful if you easily want to kick off your own jobs from your programs in a flexible way.

This guide explains how to obtain an API key and use the API to start conversations.

## Obtaining an API Key

To use the OpenHands Cloud API, you'll need to generate an API key:

1. Log in to your [OpenHands Cloud](https://app.all-hands.dev) account
2. Navigate to the Settings page by clicking on your profile icon in the bottom-left corner
3. In the Settings window, locate the "API Keys" section
4. Click "Generate New Key"
5. Give your key a descriptive name (e.g., "Development", "Production")
6. Copy the generated API key and store it securely - it will only be shown once

![API Key Generation](/img/docs/api-key-generation.png)

## API Usage

### Authentication

All API requests must include your API key in the `Authorization` header:

```
Authorization: Bearer YOUR_API_KEY
```

### Starting a New Conversation

To start a new conversation with OpenHands, you'll need to make a POST request to the conversation endpoint.

#### Endpoint

```
POST https://api.all-hands.dev/api/v1/conversations
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | Yes | The initial message to start the conversation |
| `repository_url` | string | No | GitHub repository URL to provide context (must be a repository you've granted access to) |
| `model` | string | No | The model to use (defaults to the best available model) |

#### Examples

<details>
<summary>cURL</summary>

```bash
curl -X POST "https://api.all-hands.dev/api/v1/conversations" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Help me understand how to implement a React component that displays a counter",
    "repository_url": "https://github.com/yourusername/your-repo"
  }'
```
</details>

<details>
<summary>Python (with requests)</summary>

```python
import requests

api_key = "YOUR_API_KEY"
url = "https://api.all-hands.dev/api/v1/conversations"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "message": "Help me understand how to implement a React component that displays a counter",
    "repository_url": "https://github.com/yourusername/your-repo"
}

response = requests.post(url, headers=headers, json=data)
conversation = response.json()

print(f"Conversation ID: {conversation['id']}")
print(f"Status: {conversation['status']}")
```
</details>

<details>
<summary>TypeScript/JavaScript (with fetch)</summary>

```typescript
const apiKey = "YOUR_API_KEY";
const url = "https://api.all-hands.dev/api/v1/conversations";

const headers = {
  "Authorization": `Bearer ${apiKey}`,
  "Content-Type": "application/json"
};

const data = {
  message: "Help me understand how to implement a React component that displays a counter",
  repository_url: "https://github.com/yourusername/your-repo"
};

async function startConversation() {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(data)
    });

    const conversation = await response.json();

    console.log(`Conversation ID: ${conversation.id}`);
    console.log(`Status: ${conversation.status}`);

    return conversation;
  } catch (error) {
    console.error("Error starting conversation:", error);
  }
}

startConversation();
```
</details>

#### Response

The API will return a JSON object with details about the created conversation:

```json
{
  "id": "f03e31ed50f4417cb637aa1e4806269f",
  "status": "in_progress",
  "created_at": "2025-04-28T18:30:00Z",
  "updated_at": "2025-04-28T18:30:00Z",
  "message": "Help me understand how to implement a React component that displays a counter",
  "repository_url": "https://github.com/yourusername/your-repo",
  "url": "https://app.all-hands.dev/conversations/f03e31ed50f4417cb637aa1e4806269f"
}
```

### Retrieving Conversation Status

You can check the status of a conversation by making a GET request to the conversation endpoint.

#### Endpoint

```
GET https://api.all-hands.dev/api/v1/conversations/{conversation_id}
```

#### Example

<details>
<summary>cURL</summary>

```bash
curl -X GET "https://api.all-hands.dev/api/v1/conversations/f03e31ed50f4417cb637aa1e4806269f" \
  -H "Authorization: Bearer YOUR_API_KEY"
```
</details>

#### Response

```json
{
  "id": "f03e31ed50f4417cb637aa1e4806269f",
  "status": "completed",
  "created_at": "2025-04-28T18:30:00Z",
  "updated_at": "2025-04-28T18:35:00Z",
  "message": "Help me understand how to implement a React component that displays a counter",
  "repository_url": "https://github.com/yourusername/your-repo",
  "url": "https://app.all-hands.dev/conversations/f03e31ed50f4417cb637aa1e4806269f"
}
```

## Rate Limits

The API has a limit of 3 simultaneous conversations per account. If you need a higher limit for your use case, please contact us at [contact@all-hands.dev](mailto:contact@all-hands.dev).

If you exceed this limit, the API will return a 429 Too Many Requests response.

## Additional Resources

For more detailed information about the API, refer to the [OpenHands API Reference](https://docs.all-hands.dev/swagger-ui/).
