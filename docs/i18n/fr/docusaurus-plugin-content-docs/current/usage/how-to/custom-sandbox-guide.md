# Sandbox personnalisé

:::note
Ce guide est destiné aux utilisateurs qui souhaitent utiliser leur propre image Docker personnalisée pour l'environnement d'exécution. Par exemple, avec certains outils ou langages de programmation préinstallés.
:::

Le sandbox est l'endroit où l'agent effectue ses tâches. Au lieu d'exécuter des commandes directement sur votre ordinateur (ce qui pourrait être risqué), l'agent les exécute à l'intérieur d'un conteneur Docker.

Le sandbox OpenHands par défaut (`python-nodejs:python3.12-nodejs22` de [nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)) est livré avec certains packages installés comme python et Node.js, mais peut nécessiter d'autres logiciels installés par défaut.

Vous avez deux options pour la personnalisation :

- Utiliser une image existante avec les logiciels requis.
- Créer votre propre image Docker personnalisée.

Si vous choisissez la première option, vous pouvez ignorer la section `Créer votre image Docker`.

## Créer votre image Docker

Pour créer une image Docker personnalisée, elle doit être basée sur Debian.

Par exemple, si vous voulez qu'OpenHands ait `ruby` installé, vous pourriez créer un `Dockerfile` avec le contenu suivant :

```dockerfile
FROM nikolaik/python-nodejs:python3.12-nodejs22

# Install required packages
RUN apt-get update && apt-get install -y ruby
```

Ou vous pourriez utiliser une image de base spécifique à Ruby :

```dockerfile
FROM ruby:latest
```

Enregistrez ce fichier dans un dossier. Ensuite, construisez votre image Docker (par exemple, nommée custom-image) en naviguant vers le dossier dans le terminal et en exécutant :
```bash
docker build -t custom-image .
```

Cela produira une nouvelle image appelée `custom-image`, qui sera disponible dans Docker.

## Utilisation de la commande Docker

Lorsque vous exécutez OpenHands en utilisant [la commande docker](/modules/usage/installation#start-the-app), remplacez `-e SANDBOX_RUNTIME_CONTAINER_IMAGE=...` par `-e SANDBOX_BASE_CONTAINER_IMAGE=<nom de l'image personnalisée>` :

```commandline
docker run -it --rm --pull=always \
    -e SANDBOX_BASE_CONTAINER_IMAGE=custom-image \
    ...
```

## Utilisation du flux de travail de développement

### Configuration

Tout d'abord, assurez-vous de pouvoir exécuter OpenHands en suivant les instructions dans [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

### Spécifier l'image de base du Sandbox

Dans le fichier `config.toml` du répertoire OpenHands, définissez `base_container_image` sur l'image que vous souhaitez utiliser. Il peut s'agir d'une image que vous avez déjà téléchargée ou que vous avez construite :

```bash
[core]
...
[sandbox]
base_container_image="custom-image"
```

### Options de configuration supplémentaires

Le fichier `config.toml` prend en charge plusieurs autres options pour personnaliser votre sandbox :

```toml
[core]
# Install additional dependencies when the runtime is built
# Can contain any valid shell commands
# If you need the path to the Python interpreter in any of these commands, you can use the $OH_INTERPRETER_PATH variable
runtime_extra_deps = """
pip install numpy pandas
apt-get update && apt-get install -y ffmpeg
"""

# Set environment variables for the runtime
# Useful for configuration that needs to be available at runtime
runtime_startup_env_vars = { DATABASE_URL = "postgresql://user:pass@localhost/db" }

# Specify platform for multi-architecture builds (e.g., "linux/amd64" or "linux/arm64")
platform = "linux/amd64"
```

### Exécution

Exécutez OpenHands en lançant ```make run``` dans le répertoire principal.
