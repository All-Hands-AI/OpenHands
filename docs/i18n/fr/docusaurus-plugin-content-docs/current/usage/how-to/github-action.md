# Utilisation de l'Action GitHub OpenHands

Ce guide explique comment utiliser l'Action GitHub OpenHands dans vos propres projets.

## Utilisation de l'Action dans le Dépôt OpenHands

Pour utiliser l'Action GitHub OpenHands dans un dépôt, vous pouvez :

1. Créer une issue dans le dépôt.
2. Ajouter l'étiquette `fix-me` à l'issue ou laisser un commentaire sur l'issue commençant par `@openhands-agent`.

L'action se déclenchera automatiquement et tentera de résoudre l'issue.

## Installation de l'Action dans un Nouveau Dépôt

Pour installer l'Action GitHub OpenHands dans votre propre dépôt, suivez
le [README du Résolveur OpenHands](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md).

## Conseils d'Utilisation

### Résolution itérative

1. Créez une issue dans le dépôt.
2. Ajoutez l'étiquette `fix-me` à l'issue, ou laissez un commentaire commençant par `@openhands-agent`.
3. Examinez la tentative de résolution de l'issue en vérifiant la pull request.
4. Donnez votre feedback via des commentaires généraux, des commentaires de révision ou des commentaires en ligne.
5. Ajoutez l'étiquette `fix-me` à la pull request, ou répondez à un commentaire spécifique en commençant par `@openhands-agent`.

### Étiquette versus Macro

- Étiquette (`fix-me`) : Demande à OpenHands de traiter **l'ensemble** de l'issue ou de la pull request.
- Macro (`@openhands-agent`) : Demande à OpenHands de considérer uniquement la description de l'issue/pull request et **le commentaire spécifique**.

## Paramètres Avancés

### Ajouter des paramètres personnalisés au dépôt

Vous pouvez fournir des instructions personnalisées pour OpenHands en suivant le [README du résolveur](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md#providing-custom-instructions).

### Configurations personnalisées

Le résolveur GitHub vérifiera automatiquement les [secrets du dépôt](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions?tool=webui#creating-secrets-for-a-repository) valides ou les [variables du dépôt](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#creating-configuration-variables-for-a-repository) pour personnaliser son comportement.
Les options de personnalisation que vous pouvez définir sont :

| **Nom de l'attribut**            | **Type** | **Objectif**                                                                                         | **Exemple**                                        |
| -------------------------------- | -------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `LLM_MODEL`                      | Variable | Définir le LLM à utiliser avec OpenHands                                                             | `LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"` |
| `OPENHANDS_MAX_ITER`             | Variable | Définir la limite maximale d'itérations de l'agent                                                   | `OPENHANDS_MAX_ITER=10`                            |
| `OPENHANDS_MACRO`                | Variable | Personnaliser la macro par défaut pour invoquer le résolveur                                         | `OPENHANDS_MACRO=@resolveit`                       |
| `OPENHANDS_BASE_CONTAINER_IMAGE` | Variable | Sandbox personnalisé ([en savoir plus](https://docs.all-hands.dev/modules/usage/how-to/custom-sandbox-guide)) | `OPENHANDS_BASE_CONTAINER_IMAGE="custom_image"`    |
| `TARGET_BRANCH`                  | Variable | Fusionner vers une branche autre que `main`                                                          | `TARGET_BRANCH="dev"`                              |
