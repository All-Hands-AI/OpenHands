

# Mode CLI

OpenHands peut être exécuté en mode CLI interactif, ce qui permet aux utilisateurs de démarrer une session interactive via la ligne de commande.

Ce mode est différent du [mode headless](headless-mode), qui est non interactif et mieux adapté aux scripts.

## Avec Python

Pour démarrer une session OpenHands interactive via la ligne de commande, suivez ces étapes :

1. Assurez-vous d'avoir suivi les [instructions de configuration de développement](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

2. Exécutez la commande suivante :

```bash
poetry run python -m openhands.core.cli
```

Cette commande démarrera une session interactive où vous pourrez saisir des tâches et recevoir des réponses d'OpenHands.

Vous devrez vous assurer de définir votre modèle, votre clé API et d'autres paramètres via des variables d'environnement
[ou le fichier `config.toml`](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).


## Avec Docker

Pour exécuter OpenHands en mode CLI avec Docker, suivez ces étapes :

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
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.20 \
    python -m openhands.core.cli
```

Cette commande démarrera une session interactive dans Docker où vous pourrez saisir des tâches et recevoir des réponses d'OpenHands.

## Exemples de commandes CLI et de sorties attendues

Voici quelques exemples de commandes CLI et leurs sorties attendues :

### Exemple 1 : Tâche simple

```bash
How can I help? >> Écrivez un script Python qui affiche "Hello, World!"
```

Sortie attendue :

```bash
🤖 Bien sûr ! Voici un script Python qui affiche "Hello, World!" :

❯ print("Hello, World!")
```

### Exemple 2 : Commande Bash

```bash
How can I help? >> Créez un répertoire nommé "test_dir"
```

Sortie attendue :

```bash
🤖 Création d'un répertoire nommé "test_dir" :

❯ mkdir test_dir
```

### Exemple 3 : Gestion des erreurs

```bash
How can I help? >> Supprimez un fichier inexistant
```

Sortie attendue :

```bash
🤖 Une erreur s'est produite. Veuillez réessayer.
```
