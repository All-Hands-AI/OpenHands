

# Mode sans interface

Vous pouvez exécuter OpenHands avec une seule commande, sans démarrer l'application web.
Cela facilite l'écriture de scripts et l'automatisation des tâches avec OpenHands.

Ceci est différent du [Mode CLI](cli-mode), qui est interactif et mieux adapté au développement actif.

## Avec Python

Pour exécuter OpenHands en mode sans interface avec Python,
[suivez les instructions de configuration de développement](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md),
puis exécutez :

```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

Vous devrez vous assurer de définir votre modèle, votre clé API et d'autres paramètres via des variables d'environnement
[ou le fichier `config.toml`](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).

## Avec Docker

1. Définissez `WORKSPACE_BASE` sur le répertoire que vous voulez qu'OpenHands modifie :

```bash
WORKSPACE_BASE=$(pwd)/workspace
```

2. Définissez `LLM_MODEL` sur le modèle que vous voulez utiliser :

```bash
LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"

```

3. Définissez `LLM_API_KEY` sur votre clé API :

```bash
LLM_API_KEY="sk_test_12345"
```

4. Exécutez la commande Docker suivante :

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.20-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -e LOG_ALL_EVENTS=true \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.20 \
    python -m openhands.core.main -t "write a bash script that prints hi" --no-auto-continue
```
