# 💿 Comment Créer un Soutien Docker sur Mesure

Le sandbox par défaut OpenDevin est équipé d'une configuration ubuntu minimaliste. Votre cas d'utilisation pourrait nécessiter des logiciels installés par défaut. Cet article vous enseignera comment réaliser cela en utilisant une image docker personnalisée.

## Configuration

Assurez-vous de pouvoir utiliser OpenDevin en suivant la documentation [Development.md](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md).

## Créer Votre Image Docker

Ensuite, vous devez créer votre image docker personnalisée qui doit être basée sur debian/ubuntu. Par exemple, si nous souhaitons que OpenDevin ait accès au "node" binaire, nous utiliserions ce Dockerfile:

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

> Remarque: Dans la configuration décrite ici, OpenDevin va fonctionner en tant que utilisateur "opendevin" à l'intérieur du sandbox et donc tous les packages installés via le Dockerfile seront disponibles pour tous les utilisateurs sur le système, pas seulement root.
>
> L'installation avec apt-get ci-dessus installe nodejs pour tous les utilisateurs.

## Spécifiez votre image personnalisée dans le fichier config.toml

La configuration OpenDevin se fait via le fichier de niveau supérieur ```config.toml``` .
Créez un fichier ```config.toml``` dans le répertoire OpenDevin et entrez ces contenus:

```toml
[core]
workspace_base="./workspace"
persist_sandbox=false
run_as_devin=true
sandbox_container_image="image_personnalisée"
```

> Assurez-vous que ```sandbox_container_image``` est défini sur le nom de votre image personnalisée précédente.

## Exécution

Exécutez OpenDevin en exécutant ```make run``` dans le répertoire racine.

Naviguez vers ```localhost:3001``` et vérifiez si vos dépendances souhaitées sont disponibles.

Dans le cas de l'exemple ci-dessus, la commande ```node -v``` dans la console produit ```v18.19.1```

Félicitations !

## Explication technique

Le code pertinent est défini dans [ssh_box.py](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/ssh_box.py) et [image_agnostic_util.py](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/image_agnostic_util.py).

En particulier, ssh_box.py vérifie l'objet config pour ```config.sandbox_container_image``` et ensuite tente de récupérer l'image à l'aide de [get_od_sandbox_image](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/image_agnostic_util.py#L72), qui est défini dans image_agnostic_util.py.

Lorsqu'une image personnalisée est utilisée pour la première fois, elle ne sera pas trouvée et donc elle sera construite (à l'exécution ultérieure, l'image construite sera trouvée et renvoyée).

L'image personnalisée est construite avec [_build_sandbox_image()](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/image_agnostic_util.py#L29), qui crée un fichier docker en utilisant votre image personnalisée comme base et configure ensuite l'environnement pour OpenDevin, comme ceci:

```python
dockerfile_content = (
        f'FROM {base_image}\n'
        'RUN apt update && apt install -y openssh-server wget sudo\n'
        'RUN mkdir -p -m0755 /var/run/sshd\n'
        'RUN mkdir -p /opendevin && mkdir -p /opendevin/logs && chmod 777 /opendevin/logs\n'
        'RUN wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"\n'
        'RUN bash Miniforge3-$(uname)-$(uname -m).sh -b -p /opendevin/miniforge3\n'
        'RUN bash -c ". /opendevin/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"\n'
        'RUN echo "export PATH=/opendevin/miniforge3/bin:$PATH" >> ~/.bashrc\n'
        'RUN echo "export PATH=/opendevin/miniforge3/bin:$PATH" >> /opendevin/bash.bashrc\n'
    ).strip()
```

> Remarque: Le nom de l'image est modifié via [_get_new_image_name()](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/image_agnostic_util.py#L63) et c'est ce nom modifié qui sera recherché lors des exécutions ultérieures.

## Dépannage / Erreurs

### Erreur: ```useradd: UID 1000 est non unique```
Si vous voyez cette erreur dans la sortie de la console, il s'agit du fait que OpenDevin essaie de créer le utilisateur opendevin dans le sandbox avec un ID d'utilisateur de 1000, cependant cet ID d'utilisateur est déjà utilisé dans l'image (pour une raison inconnue). Pour résoudre ce problème, changez la valeur du champ sandbox_user_id dans le fichier config.toml en une valeur différente:

```toml
[core]
workspace_base="./workspace"
persist_sandbox=false
run_as_devin=true
sandbox_container_image="image_personnalisée"
sandbox_user_id="1001"
```

### Erreurs de port d'utilisation

Si vous voyez un message d'erreur indiquant que le port est utilisé ou indisponible, essayez de supprimer toutes les containers docker en cours d'exécution (exécutez `docker ps` et `docker rm` des containers concernés) puis ré-exécutez ```make run```

## Discuter

Pour d'autres problèmes ou questions rejoignez le [Slack](https://join.slack.com/t/opendevin/shared_invite/zt-2ngejmfw6-9gW4APWOC9XUp1n~SiQ6iw) ou le [Discord](https://discord.gg/ESHStjSjD4) et demandez!
