# 💿 Comment Créer un Soutien Docker sur Mesure

Le sandbox par défaut OpenHands est équipé d'une configuration ubuntu minimaliste. Votre cas d'utilisation pourrait nécessiter des logiciels installés par défaut. Cet article vous enseignera comment réaliser cela en utilisant une image docker personnalisée.

## Configuration

Assurez-vous de pouvoir utiliser OpenHands en suivant la documentation [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

## Créer Votre Image Docker

Ensuite, vous devez créer votre image docker personnalisée qui doit être basée sur debian/ubuntu. Par exemple, si nous souhaitons que OpenHands ait accès au "node" binaire, nous utiliserions ce Dockerfile:

```bash
# Commencez avec l'image ubuntu la plus récente
FROM ubuntu:latest

# Effectuez les mises à jour nécessaires
RUN apt-get update && apt-get install

# Installez nodejs
RUN apt-get install -y nodejs
```

Ensuite, construisez votre image docker avec le nom de votre choix. Par exemple "image_personnalisée". Pour cela, créez un répertoire et placez le fichier à l'intérieur avec le nom "Dockerfile", puis dans le répertoire exécutez cette commande:

```bash
docker build -t image_personnalisée .
```

Cela produira une nouvelle image appelée ```image_personnalisée``` qui sera disponible dans Docker Engine.

> Remarque: Dans la configuration décrite ici, OpenHands va fonctionner en tant que utilisateur "openhands" à l'intérieur du sandbox et donc tous les packages installés via le Dockerfile seront disponibles pour tous les utilisateurs sur le système, pas seulement root.
>
> L'installation avec apt-get ci-dessus installe nodejs pour tous les utilisateurs.

## Spécifiez votre image personnalisée dans le fichier config.toml

La configuration OpenHands se fait via le fichier de niveau supérieur ```config.toml``` .
Créez un fichier ```config.toml``` dans le répertoire OpenHands et entrez ces contenus:

```toml
[core]
workspace_base="./workspace"
run_as_openhands=true
[sandbox]
base_container_image="image_personnalisée"
```

> Assurez-vous que ```base_container_image``` est défini sur le nom de votre image personnalisée précédente.

## Exécution

Exécutez OpenHands en exécutant ```make run``` dans le répertoire racine.

Naviguez vers ```localhost:3001``` et vérifiez si vos dépendances souhaitées sont disponibles.

Dans le cas de l'exemple ci-dessus, la commande ```node -v``` dans la console produit ```v18.19.1```

Félicitations !

## Explication technique

Veuillez consulter le [chapitre sur les images Docker personnalisées dans la documentation d'exécution](https://docs.all-hands.dev/fr/modules/usage/architecture/runtime) pour obtenir des explications plus détaillées.

## Dépannage / Erreurs

### Erreur: ```useradd: UID 1000 est non unique```
Si vous voyez cette erreur dans la sortie de la console, il s'agit du fait que OpenHands essaie de créer le utilisateur openhands dans le sandbox avec un ID d'utilisateur de 1000, cependant cet ID d'utilisateur est déjà utilisé dans l'image (pour une raison inconnue). Pour résoudre ce problème, changez la valeur du champ user_id dans le fichier config.toml en une valeur différente:

```toml
[core]
workspace_base="./workspace"
run_as_openhands=true
[sandbox]
base_container_image="image_personnalisée"
user_id="1001"
```

### Erreurs de port d'utilisation

Si vous voyez un message d'erreur indiquant que le port est utilisé ou indisponible, essayez de supprimer toutes les containers docker en cours d'exécution (exécutez `docker ps` et `docker rm` des containers concernés) puis ré-exécutez ```make run```
