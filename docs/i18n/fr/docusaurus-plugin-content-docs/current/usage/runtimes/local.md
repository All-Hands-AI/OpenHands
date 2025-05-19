# Runtime Local

Le Runtime Local permet à l'agent OpenHands d'exécuter des actions directement sur votre machine locale sans utiliser Docker.
Ce runtime est principalement destiné aux environnements contrôlés comme les pipelines CI ou les scénarios de test où Docker n'est pas disponible.

:::caution
**Avertissement de sécurité** : Le Runtime Local s'exécute sans aucune isolation sandbox. L'agent peut directement accéder et modifier
des fichiers sur votre machine. N'utilisez ce runtime que dans des environnements contrôlés ou lorsque vous comprenez pleinement les implications de sécurité.
:::

## Prérequis

Avant d'utiliser le Runtime Local, assurez-vous que :

1. Vous pouvez exécuter OpenHands en utilisant le [workflow de développement](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
2. tmux est disponible sur votre système.

## Configuration

Pour utiliser le Runtime Local, en plus des configurations requises comme le fournisseur LLM, le modèle et la clé API, vous devrez définir
les options suivantes via des variables d'environnement ou le [fichier config.toml](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml) lors du démarrage d'OpenHands :

Via des variables d'environnement :

```bash
# Requis
export RUNTIME=local

# Optionnel mais recommandé
# L'agent travaille dans /workspace par défaut, donc montez votre répertoire de projet à cet endroit
export SANDBOX_VOLUMES=/chemin/vers/votre/espace_de_travail:/workspace:rw
# Pour des données en lecture seule, utilisez un chemin de montage différent
# export SANDBOX_VOLUMES=/chemin/vers/votre/espace_de_travail:/workspace:rw,/chemin/vers/grand/dataset:/data:ro
```

Via `config.toml` :

```toml
[core]
runtime = "local"

[sandbox]
# L'agent travaille dans /workspace par défaut, donc montez votre répertoire de projet à cet endroit
volumes = "/chemin/vers/votre/espace_de_travail:/workspace:rw"
# Pour des données en lecture seule, utilisez un chemin de montage différent
# volumes = "/chemin/vers/votre/espace_de_travail:/workspace:rw,/chemin/vers/grand/dataset:/data:ro"
```

Si `SANDBOX_VOLUMES` n'est pas défini, le runtime créera un répertoire temporaire pour que l'agent y travaille.

## Exemple d'utilisation

Voici un exemple de démarrage d'OpenHands avec le Runtime Local en Mode Headless :

```bash
# Définir le type de runtime sur local
export RUNTIME=local

# Définir un répertoire de travail (l'agent travaille dans /workspace par défaut)
export SANDBOX_VOLUMES=/chemin/vers/votre/projet:/workspace:rw
# Pour des données en lecture seule que vous ne voulez pas que l'agent modifie, utilisez un chemin différent
# export SANDBOX_VOLUMES=/chemin/vers/votre/projet:/workspace:rw,/chemin/vers/données/référence:/data:ro

# Démarrer OpenHands
poetry run python -m openhands.core.main -t "écrire un script bash qui affiche bonjour"
```

## Cas d'utilisation

Le Runtime Local est particulièrement utile pour :

- Les pipelines CI/CD où Docker n'est pas disponible.
- Les tests et le développement d'OpenHands lui-même.
- Les environnements où l'utilisation de conteneurs est restreinte.
