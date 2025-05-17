# OpenHands Cloud API

OpenHands Cloudは、サービスをプログラムで操作できるREST APIを提供しています。これは、自分のプログラムから柔軟な方法で簡単にジョブを開始したい場合に便利です。

このガイドでは、APIキーの取得方法と、APIを使用して会話を開始する方法について説明します。
APIの詳細については、[OpenHands APIリファレンス](https://docs.all-hands.dev/swagger-ui/)を参照してください。

## APIキーの取得

OpenHands Cloud APIを使用するには、APIキーを生成する必要があります：

1. [OpenHands Cloud](https://app.all-hands.dev)アカウントにログインします
2. [設定ページ](https://app.all-hands.dev/settings)に移動します
3. 「APIキー」セクションを見つけます
4. 「新しいキーを生成」をクリックします
5. キーに分かりやすい名前を付けます（例：「開発用」、「本番用」）
6. 生成されたAPIキーをコピーして安全に保管します - 表示されるのは一度だけです

![APIキー生成](/img/docs/api-key-generation.png)

## APIの使用方法

### 新しい会話の開始

OpenHandsでタスクを実行する新しい会話を開始するには、会話エンドポイントにPOSTリクエストを送信する必要があります。

#### リクエストパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|------|----------|-------------|
| `initial_user_msg` | string | はい | 会話を開始する最初のメッセージ |
| `repository` | string | いいえ | コンテキストを提供するGitリポジトリ名（`owner/repo`形式）。リポジトリへのアクセス権が必要です。 |

#### 例

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
<summary>Python (requestsを使用)</summary>

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
<summary>TypeScript/JavaScript (fetchを使用)</summary>

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

#### レスポンス

APIは作成された会話の詳細を含むJSONオブジェクトを返します：

```json
{
  "status": "ok",
  "conversation_id": "abc1234",
}
```

以下の場合は`AuthenticationError`を受け取ることがあります：

1. 無効なAPIキーを提供した場合
2. 間違ったリポジトリ名を提供した場合
3. リポジトリへのアクセス権がない場合


### 会話ステータスの取得

会話エンドポイントにGETリクエストを送信することで、会話のステータスを確認できます。

#### エンドポイント

```
GET https://app.all-hands.dev/api/conversations/{conversation_id}
```

#### 例

<details>
<summary>cURL</summary>

```bash
curl -X GET "https://app.all-hands.dev/api/conversations/{conversation_id}" \
  -H "Authorization: Bearer YOUR_API_KEY"
```
</details>

#### レスポンス

レスポンスは以下の形式でフォーマットされます：

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

## レート制限

APIはアカウントごとに10の同時会話の制限があります。ユースケースに応じてより高い制限が必要な場合は、[contact@all-hands.dev](mailto:contact@all-hands.dev)までお問い合わせください。

この制限を超えると、APIは429 Too Many Requestsレスポンスを返します。
