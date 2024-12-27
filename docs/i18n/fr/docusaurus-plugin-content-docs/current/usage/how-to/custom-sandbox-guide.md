

# Sandbox Personnalisé

Le sandbox est l'endroit où l'agent effectue ses tâches. Au lieu d'exécuter des commandes directement sur votre ordinateur (ce qui pourrait être risqué), l'agent les exécute à l'intérieur d'un conteneur Docker.

Le sandbox OpenHands par défaut (`python-nodejs:python3.12-nodejs22` de [nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)) est livré avec certains paquets installés tels que Python et Node.js mais peut nécessiter l'installation d'autres logiciels par défaut.

Vous avez deux options pour la personnalisation :

1. Utiliser une image existante avec les logiciels requis.
2. Créer votre propre image Docker personnalisée.

Si vous choisissez la première option, vous pouvez passer la section `Créer Votre Image Docker`.

## Créer Votre Image Docker

Pour créer une image Docker personnalisée, elle doit être basée sur Debian.

Par exemple, si vous voulez qu'OpenHands ait `ruby` installé, créez un `Dockerfile` avec le contenu suivant :

```dockerfile
FROM debian:latest

# Installer les paquets requis
RUN apt-get update && apt-get install -y ruby
```

Enregistrez ce fichier dans un dossier. Ensuite, construisez votre image Docker (par exemple, nommée custom-image) en naviguant vers le dossier dans le terminal et en exécutant :

```bash
docker build -t custom-image .
```

Cela produira une nouvelle image appelée `custom-image`, qui sera disponible dans Docker.

> Notez que dans la configuration décrite dans ce document, OpenHands s'exécutera en tant qu'utilisateur "openhands" à l'intérieur du sandbox et donc tous les paquets installés via le docker file devraient être disponibles pour tous les utilisateurs du système, pas seulement root.

## Utilisation du Workflow de Développement

### Configuration

Tout d'abord, assurez-vous de pouvoir exécuter OpenHands en suivant les instructions dans [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

### Spécifier l'Image de Base du Sandbox

Dans le fichier `config.toml` dans le répertoire OpenHands, définissez `sandbox_base_container_image` sur l'image que vous souhaitez utiliser. Cela peut être une image que vous avez déjà extraite ou une que vous avez construite :

```bash
[core]
...
sandbox_base_container_image="custom-image"
```

### Exécution

Exécutez OpenHands en exécutant ```make run``` dans le répertoire de niveau supérieur.

## Explication Technique

Veuillez vous référer à la [section image docker personnalisée de la documentation d'exécution](https://docs.all-hands.dev/modules/usage/architecture/runtime#advanced-how-openhands-builds-and-maintains-od-runtime-images) pour plus de détails.
