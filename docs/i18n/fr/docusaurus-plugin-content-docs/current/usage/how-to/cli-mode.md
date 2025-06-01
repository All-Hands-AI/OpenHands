# Mode CLI

OpenHands peut être exécuté en mode CLI interactif, ce qui permet aux utilisateurs de démarrer une session interactive via la ligne de commande.

Ce mode est différent du [mode headless](headless-mode), qui est non interactif et mieux adapté aux scripts.

## Avec Python

Pour démarrer une session interactive OpenHands via la ligne de commande :

1. Assurez-vous d'avoir suivi les [instructions de configuration pour le développement](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
2. Exécutez la commande suivante :

```bash
poetry run python -m openhands.core.cli
```

Cette commande lancera une session interactive où vous pourrez saisir des tâches et recevoir des réponses d'OpenHands.

Vous devrez vous assurer de définir votre modèle, clé API et autres paramètres via des variables d'environnement
[ou le fichier `config.toml`](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).

## Avec Docker

Pour exécuter OpenHands en mode CLI avec Docker :

1. Définissez les variables d'environnement suivantes dans votre terminal :

- `SANDBOX_VOLUMES` pour spécifier le répertoire auquel vous souhaitez qu'OpenHands accède (Ex : `export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw`).
  - L'agent travaille dans `/workspace` par défaut, donc montez votre répertoire de projet à cet emplacement si vous souhaitez que l'agent modifie des fichiers.
  - Pour les données en lecture seule, utilisez un chemin de montage différent (Ex : `export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw,/path/to/large/dataset:/data:ro`).
- `LLM_MODEL` pour le modèle à utiliser (Ex : `export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`).
- `LLM_API_KEY` pour la clé API (Ex : `export LLM_API_KEY="sk_test_12345"`).

2. Exécutez la commande Docker suivante :

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.39-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=$SANDBOX_VOLUMES \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.39 \
    python -m openhands.core.cli
```

Cette commande lancera une session interactive dans Docker où vous pourrez saisir des tâches et recevoir des réponses d'OpenHands.

Le paramètre `-e SANDBOX_USER_ID=$(id -u)` est transmis à la commande Docker pour s'assurer que l'utilisateur du sandbox correspond aux permissions de l'utilisateur hôte. Cela empêche l'agent de créer des fichiers appartenant à root dans l'espace de travail monté.
