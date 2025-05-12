# API Cloud OpenHands

OpenHands Cloud fournit une API REST qui vous permet d'interagir programmatiquement avec le service. Cela est utile si vous souhaitez facilement lancer vos propres tâches depuis vos programmes de manière flexible.

Ce guide explique comment obtenir une clé API et utiliser l'API pour démarrer des conversations.
Pour des informations plus détaillées sur l'API, consultez la [Référence API OpenHands](https://docs.all-hands.dev/swagger-ui/).

## Obtention d'une clé API

Pour utiliser l'API OpenHands Cloud, vous devrez générer une clé API :

1. Connectez-vous à votre compte [OpenHands Cloud](https://app.all-hands.dev)
2. Accédez à la [page Paramètres](https://app.all-hands.dev/settings)
3. Localisez la section "Clés API"
4. Cliquez sur "Générer une nouvelle clé"
5. Donnez à votre clé un nom descriptif (par exemple, "Développement", "Production")
6. Copiez la clé API générée et conservez-la en lieu sûr - elle ne sera affichée qu'une seule fois

![Génération de clé API](/img/docs/api-key-generation.png)

## Utilisation de l'API

### Démarrer une nouvelle conversation

Pour démarrer une nouvelle conversation avec OpenHands effectuant une tâche, vous devrez faire une requête POST vers le point de terminaison de conversation.

#### Paramètres de la requête

| Paramètre | Type | Obligatoire | Description |
|-----------|------|-------------|-------------|
| `initial_user_msg` | chaîne | Oui | Le message initial pour démarrer la conversation |
| `repository` | chaîne | Non | Nom du dépôt Git pour fournir du contexte au format `propriétaire/repo`. Vous devez avoir accès au dépôt. |

#### Exemples

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
<summary>Python (avec requests)</summary>

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
<summary>TypeScript/JavaScript (avec fetch)</summary>

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

#### Réponse

L'API renverra un objet JSON avec les détails de la conversation créée :

```json
{
  "status": "ok",
  "conversation_id": "abc1234",
}
```

Vous pouvez également recevoir une `AuthenticationError` si :

1. Vous avez fourni une clé API invalide
2. Vous avez fourni un nom de dépôt incorrect
3. Vous n'avez pas accès au dépôt


### Récupération du statut d'une conversation

Vous pouvez vérifier le statut d'une conversation en faisant une requête GET vers le point de terminaison de conversation.

#### Point de terminaison

```
GET https://app.all-hands.dev/api/conversations/{conversation_id}
```

#### Exemple

<details>
<summary>cURL</summary>

```bash
curl -X GET "https://app.all-hands.dev/api/conversations/{conversation_id}" \
  -H "Authorization: Bearer YOUR_API_KEY"
```
</details>

#### Réponse

La réponse est formatée comme suit :

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

## Limites de taux

L'API a une limite de 10 conversations simultanées par compte. Si vous avez besoin d'une limite plus élevée pour votre cas d'utilisation, veuillez nous contacter à [contact@all-hands.dev](mailto:contact@all-hands.dev).

Si vous dépassez cette limite, l'API renverra une réponse 429 Too Many Requests.
