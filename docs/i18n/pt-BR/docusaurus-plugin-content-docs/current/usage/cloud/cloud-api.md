# API da OpenHands Cloud

A OpenHands Cloud fornece uma API REST que permite interagir programaticamente com o serviço. Isso é útil se você deseja iniciar facilmente seus próprios trabalhos a partir de seus programas de maneira flexível.

Este guia explica como obter uma chave de API e usar a API para iniciar conversas.
Para informações mais detalhadas sobre a API, consulte a [Referência da API OpenHands](https://docs.all-hands.dev/swagger-ui/).

## Obtendo uma Chave de API

Para usar a API da OpenHands Cloud, você precisará gerar uma chave de API:

1. Faça login na sua conta [OpenHands Cloud](https://app.all-hands.dev)
2. Navegue até a [página de Configurações](https://app.all-hands.dev/settings)
3. Localize a seção "API Keys"
4. Clique em "Generate New Key"
5. Dê à sua chave um nome descritivo (ex: "Desenvolvimento", "Produção")
6. Copie a chave de API gerada e armazene-a com segurança - ela será mostrada apenas uma vez

![Geração de Chave de API](/img/docs/api-key-generation.png)

## Uso da API

### Iniciando uma Nova Conversa

Para iniciar uma nova conversa com a OpenHands realizando uma tarefa, você precisará fazer uma requisição POST para o endpoint de conversas.

#### Parâmetros da Requisição

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `initial_user_msg` | string | Sim | A mensagem inicial para começar a conversa |
| `repository` | string | Não | Nome do repositório Git para fornecer contexto no formato `proprietário/repo`. Você deve ter acesso ao repositório. |

#### Exemplos

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
<summary>Python (com requests)</summary>

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
<summary>TypeScript/JavaScript (com fetch)</summary>

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

#### Resposta

A API retornará um objeto JSON com detalhes sobre a conversa criada:

```json
{
  "status": "ok",
  "conversation_id": "abc1234",
}
```

Você também pode receber um `AuthenticationError` se:

1. Você forneceu uma chave de API inválida
2. Você forneceu o nome do repositório errado
3. Você não tem acesso ao repositório


### Recuperando o Status da Conversa

Você pode verificar o status de uma conversa fazendo uma requisição GET para o endpoint de conversas.

#### Endpoint

```
GET https://app.all-hands.dev/api/conversations/{conversation_id}
```

#### Exemplo

<details>
<summary>cURL</summary>

```bash
curl -X GET "https://app.all-hands.dev/api/conversations/{conversation_id}" \
  -H "Authorization: Bearer YOUR_API_KEY"
```
</details>

#### Resposta

A resposta é formatada da seguinte forma:

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

## Limites de Taxa

A API tem um limite de 10 conversas simultâneas por conta. Se você precisar de um limite maior para seu caso de uso, entre em contato conosco em [contact@all-hands.dev](mailto:contact@all-hands.dev).

Se você exceder esse limite, a API retornará uma resposta 429 Too Many Requests.
