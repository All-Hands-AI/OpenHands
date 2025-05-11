# Protocole de Contexte de Modèle (MCP)

:::note
Cette page explique comment configurer et utiliser le Protocole de Contexte de Modèle (MCP) dans OpenHands, vous permettant d'étendre les capacités de l'agent avec des outils personnalisés.
:::

## Aperçu

Le Protocole de Contexte de Modèle (MCP) est un mécanisme qui permet à OpenHands de communiquer avec des serveurs d'outils externes. Ces serveurs peuvent fournir des fonctionnalités supplémentaires à l'agent, comme le traitement spécialisé de données, l'accès à des API externes, ou des outils personnalisés. MCP est basé sur le standard ouvert défini sur [modelcontextprotocol.io](https://modelcontextprotocol.io).

## Configuration

La configuration MCP est définie dans la section `[mcp]` de votre fichier `config.toml`.

### Exemple de configuration

```toml
[mcp]
# Serveurs SSE - Serveurs externes qui communiquent via Server-Sent Events
sse_servers = [
    # Serveur SSE basique avec juste une URL
    "http://example.com:8080/mcp",

    # Serveur SSE avec authentification par clé API
    {url="https://secure-example.com/mcp", api_key="your-api-key"}
]

# Serveurs Stdio - Processus locaux qui communiquent via entrée/sortie standard
stdio_servers = [
    # Serveur stdio basique
    {name="fetch", command="uvx", args=["mcp-server-fetch"]},

    # Serveur stdio avec variables d'environnement
    {
        name="data-processor",
        command="python",
        args=["-m", "my_mcp_server"],
        env={
            "DEBUG": "true",
            "PORT": "8080"
        }
    }
]
```

## Options de configuration

### Serveurs SSE

Les serveurs SSE sont configurés en utilisant soit une URL sous forme de chaîne, soit un objet avec les propriétés suivantes :

- `url` (obligatoire)
  - Type: `str`
  - Description: L'URL du serveur SSE

- `api_key` (optionnel)
  - Type: `str`
  - Par défaut: `None`
  - Description: Clé API pour l'authentification avec le serveur SSE

### Serveurs Stdio

Les serveurs Stdio sont configurés en utilisant un objet avec les propriétés suivantes :

- `name` (obligatoire)
  - Type: `str`
  - Description: Un nom unique pour le serveur

- `command` (obligatoire)
  - Type: `str`
  - Description: La commande pour exécuter le serveur

- `args` (optionnel)
  - Type: `list of str`
  - Par défaut: `[]`
  - Description: Arguments de ligne de commande à passer au serveur

- `env` (optionnel)
  - Type: `dict of str to str`
  - Par défaut: `{}`
  - Description: Variables d'environnement à définir pour le processus du serveur

## Comment fonctionne MCP

Lorsque OpenHands démarre, il :

1. Lit la configuration MCP depuis `config.toml`
2. Se connecte à tous les serveurs SSE configurés
3. Démarre tous les serveurs stdio configurés
4. Enregistre les outils fournis par ces serveurs auprès de l'agent

L'agent peut alors utiliser ces outils comme n'importe quel outil intégré. Lorsque l'agent appelle un outil MCP :

1. OpenHands achemine l'appel vers le serveur MCP approprié
2. Le serveur traite la demande et renvoie une réponse
3. OpenHands convertit la réponse en une observation et la présente à l'agent
