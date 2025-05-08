# Docker Runtime

C'est le Runtime par défaut qui est utilisé lorsque vous démarrez OpenHands.

## Image
Le `SANDBOX_RUNTIME_CONTAINER_IMAGE` de nikolaik est une image runtime pré-construite
qui contient notre serveur Runtime, ainsi que quelques utilitaires de base pour Python et NodeJS.
Vous pouvez également [construire votre propre image runtime](../how-to/custom-sandbox-guide).

## Connexion à votre système de fichiers
Une fonctionnalité utile est la possibilité de se connecter à votre système de fichiers local. Pour monter votre système de fichiers dans le runtime :

### Utilisation de SANDBOX_VOLUMES

La façon la plus simple de monter votre système de fichiers local est d'utiliser la variable d'environnement `SANDBOX_VOLUMES` :

```bash
docker run # ...
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=/path/to/your/code:/workspace:rw \
    # ...
```

Le format de `SANDBOX_VOLUMES` est : `chemin_hôte:chemin_conteneur[:mode]`

- `chemin_hôte` : Le chemin sur votre machine hôte que vous souhaitez monter
- `chemin_conteneur` : Le chemin à l'intérieur du conteneur où le chemin de l'hôte sera monté
  - Utilisez `/workspace` pour les fichiers que vous voulez que l'agent modifie. L'agent travaille dans `/workspace` par défaut.
  - Utilisez un chemin différent (par exemple, `/data`) pour les documents de référence en lecture seule ou les grands ensembles de données
- `mode` : Mode de montage optionnel, soit `rw` (lecture-écriture, par défaut) soit `ro` (lecture seule)

Vous pouvez également spécifier plusieurs montages en les séparant par des virgules (`,`) :

```bash
export SANDBOX_VOLUMES=/path1:/workspace/path1,/path2:/workspace/path2:ro
```

Exemples :

```bash
# Exemple Linux et Mac - Espace de travail modifiable
export SANDBOX_VOLUMES=$HOME/OpenHands:/workspace:rw

# Exemple WSL sur Windows - Espace de travail modifiable
export SANDBOX_VOLUMES=/mnt/c/dev/OpenHands:/workspace:rw

# Exemple de code de référence en lecture seule
export SANDBOX_VOLUMES=/path/to/reference/code:/data:ro

# Exemple de montages multiples - Espace de travail modifiable avec données de référence en lecture seule
export SANDBOX_VOLUMES=$HOME/projects:/workspace:rw,/path/to/large/dataset:/data:ro
```

> **Remarque :** Lors de l'utilisation de plusieurs montages, le premier montage est considéré comme l'espace de travail principal et sera utilisé pour la compatibilité avec les outils qui s'attendent à un espace de travail unique.

> **Important :** L'agent travaillera dans `/workspace` par défaut. Si vous voulez que l'agent modifie des fichiers dans votre répertoire local, vous devriez monter ce répertoire sur `/workspace`. Si vous avez des données en lecture seule que vous voulez que l'agent accède mais ne modifie pas, montez-les sur un chemin différent (comme `/data`) et demandez explicitement à l'agent de regarder à cet endroit.

### Utilisation des variables WORKSPACE_* (Déprécié)

> **Remarque :** Cette méthode est dépréciée et sera supprimée dans une version future. Veuillez utiliser `SANDBOX_VOLUMES` à la place.

1. Définissez `WORKSPACE_BASE` :

    ```bash
    export WORKSPACE_BASE=/path/to/your/code
    ```

2. Ajoutez les options suivantes à la commande `docker run` :

    ```bash
    docker run # ...
        -e SANDBOX_USER_ID=$(id -u) \
        -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
        -v $WORKSPACE_BASE:/opt/workspace_base \
        # ...
    ```

Soyez prudent ! Rien n'empêche l'agent OpenHands de supprimer ou de modifier
les fichiers qui sont montés dans son espace de travail.

Le `-e SANDBOX_USER_ID=$(id -u)` est passé à la commande Docker pour s'assurer que l'utilisateur du sandbox correspond aux
permissions de l'utilisateur hôte. Cela empêche l'agent de créer des fichiers appartenant à root dans l'espace de travail monté.

## Installation Docker renforcée

Lors du déploiement d'OpenHands dans des environnements où la sécurité est une priorité, vous devriez envisager d'implémenter une
configuration Docker renforcée. Cette section fournit des recommandations pour sécuriser votre déploiement Docker OpenHands au-delà de la configuration par défaut.

### Considérations de sécurité

La configuration Docker par défaut dans le README est conçue pour faciliter l'utilisation sur une machine de développement locale. Si vous
l'exécutez sur un réseau public (par exemple, le WiFi d'un aéroport), vous devriez mettre en œuvre des mesures de sécurité supplémentaires.

### Sécurité de liaison réseau

Par défaut, OpenHands se lie à toutes les interfaces réseau (`0.0.0.0`), ce qui peut exposer votre instance à tous les réseaux auxquels
l'hôte est connecté. Pour une configuration plus sécurisée :

1. **Restreindre la liaison réseau** : Utilisez la configuration `runtime_binding_address` pour restreindre les interfaces réseau sur lesquelles OpenHands écoute :

   ```bash
   docker run # ...
       -e SANDBOX_RUNTIME_BINDING_ADDRESS=127.0.0.1 \
       # ...
   ```

   Cette configuration garantit qu'OpenHands n'écoute que sur l'interface de bouclage (`127.0.0.1`), le rendant accessible uniquement depuis la machine locale.

2. **Liaison de port sécurisée** : Modifiez l'option `-p` pour ne se lier qu'à localhost au lieu de toutes les interfaces :

   ```bash
   docker run # ... \
       -p 127.0.0.1:3000:3000 \
   ```

   Cela garantit que l'interface web OpenHands n'est accessible que depuis la machine locale, et non depuis d'autres machines du réseau.

### Isolation réseau

Utilisez les fonctionnalités réseau de Docker pour isoler OpenHands :

```bash
# Créer un réseau isolé
docker network create openhands-network

# Exécuter OpenHands dans le réseau isolé
docker run # ... \
    --network openhands-network \
```
