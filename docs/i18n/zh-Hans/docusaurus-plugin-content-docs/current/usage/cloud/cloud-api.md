# OpenHands Cloud API

OpenHands Cloud提供了REST API，允许您以编程方式与服务交互。如果您想以灵活的方式从程序中轻松启动自己的任务，这将非常有用。

本指南解释了如何获取API密钥并使用API启动对话。
有关API的更详细信息，请参阅[OpenHands API参考](https://docs.all-hands.dev/swagger-ui/)。

## 获取API密钥

要使用OpenHands Cloud API，您需要生成一个API密钥：

1. 登录您的[OpenHands Cloud](https://app.all-hands.dev)账户
2. 导航至[设置页面](https://app.all-hands.dev/settings)
3. 找到"API密钥"部分
4. 点击"生成新密钥"
5. 为您的密钥提供一个描述性名称（例如，"开发环境"，"生产环境"）
6. 复制生成的API密钥并安全存储 - 它只会显示一次

![API密钥生成](/img/docs/api-key-generation.png)

## API使用

### 开始新对话

要开始一个新的OpenHands执行任务的对话，您需要向对话端点发送POST请求。

#### 请求参数

| 参数 | 类型 | 必需 | 描述 |
|-----------|------|----------|-------------|
| `initial_user_msg` | string | 是 | 开始对话的初始消息 |
| `repository` | string | 否 | 提供上下文的Git仓库名称，格式为`owner/repo`。您必须有权访问该仓库。 |

#### 示例

<details>
<summary>cURL</summary>

```bash
curl -X POST "https://app.all-hands.dev/api/conversations" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_user_msg": "Check whether there is any incorrect information in the README.md file and send a PR to fix it if so.",
    "repository": "yourusername/your-repo"
  }'
```
</details>

<details>
<summary>Python (with requests)</summary>

```python
import requests

api_key = "YOUR_API_KEY"
url = "https://app.all-hands.dev/api/conversations"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "initial_user_msg": "Check whether there is any incorrect information in the README.md file and send a PR to fix it if so.",
    "repository": "yourusername/your-repo"
}

response = requests.post(url, headers=headers, json=data)
conversation = response.json()

print(f"Conversation Link: https://app.all-hands.dev/conversations/{conversation['conversation_id']}")
print(f"Status: {conversation['status']}")
```
</details>

<details>
<summary>TypeScript/JavaScript (with fetch)</summary>

```typescript
const apiKey = "YOUR_API_KEY";
const url = "https://app.all-hands.dev/api/conversations";

const headers = {
  "Authorization": `Bearer ${apiKey}`,
  "Content-Type": "application/json"
};

const data = {
  initial_user_msg: "Check whether there is any incorrect information in the README.md file and send a PR to fix it if so.",
  repository: "yourusername/your-repo"
};

async function startConversation() {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(data)
    });

    const conversation = await response.json();

    console.log(`Conversation Link: https://app.all-hands.dev/conversations/${conversation.id}`);
    console.log(`Status: ${conversation.status}`);

    return conversation;
  } catch (error) {
    console.error("Error starting conversation:", error);
  }
}

startConversation();
```

</details>

#### 响应

API将返回一个包含已创建对话详情的JSON对象：

```json
{
  "status": "ok",
  "conversation_id": "abc1234",
}
```

如果出现以下情况，您可能会收到`AuthenticationError`：

1. 您提供了无效的API密钥
2. 您提供了错误的仓库名称
3. 您没有访问该仓库的权限


### 获取对话状态

您可以通过向对话端点发送GET请求来检查对话的状态。

#### 端点

```
GET https://app.all-hands.dev/api/conversations/{conversation_id}
```

#### 示例

<details>
<summary>cURL</summary>

```bash
curl -X GET "https://app.all-hands.dev/api/conversations/{conversation_id}" \
  -H "Authorization: Bearer YOUR_API_KEY"
```
</details>

#### 响应

响应格式如下：

```json
{
  "conversation_id":"abc1234",
  "title":"Update README.md",
  "created_at":"2025-04-29T15:13:51.370706Z",
  "last_updated_at":"2025-04-29T15:13:57.199210Z",
  "status":"RUNNING",
  "selected_repository":"yourusername/your-repo",
  "trigger":"gui"
}
```

## 速率限制

API对每个账户有10个同时对话的限制。如果您的使用场景需要更高的限制，请通过[contact@all-hands.dev](mailto:contact@all-hands.dev)联系我们。

如果您超过此限制，API将返回429 Too Many Requests响应。
