# Résolveur de Problèmes Cloud

Le Résolveur de Problèmes Cloud automatise les corrections de code et fournit une assistance intelligente pour vos dépôts sur GitHub et GitLab.

## Configuration

Le Résolveur de Problèmes Cloud est disponible automatiquement lorsque vous accordez l'accès au dépôt OpenHands Cloud :
- [Accès au dépôt GitHub](./github-installation#adding-repository-access)
- [Accès au dépôt GitLab](./gitlab-installation#adding-repository-access)

![Ajout d'accès au dépôt à OpenHands](/img/cloud/add-repo.png)

## Utilisation

Après avoir accordé l'accès au dépôt OpenHands Cloud, vous pouvez utiliser le Résolveur de Problèmes Cloud sur les problèmes et les pull/merge requests dans vos dépôts.

### Travailler avec les Problèmes

Sur votre dépôt, étiquetez un problème avec `openhands` ou ajoutez un message commençant par `@openhands`. OpenHands va :
1. Commenter le problème pour vous faire savoir qu'il y travaille
   - Vous pouvez cliquer sur le lien pour suivre la progression sur OpenHands Cloud
2. Ouvrir une pull request (GitHub) ou une merge request (GitLab) s'il détermine que le problème a été résolu avec succès
3. Commenter le problème avec un résumé des tâches effectuées et un lien vers la PR/MR

![Résolveur de problèmes OpenHands en action](/img/cloud/issue-resolver.png)

#### Exemples de Commandes pour les Problèmes

Voici quelques exemples de commandes que vous pouvez utiliser avec le résolveur de problèmes :

```
@openhands lisez la description du problème et corrigez-le
```

### Travailler avec les Pull/Merge Requests

Pour qu'OpenHands travaille sur les pull requests (GitHub) ou les merge requests (GitLab), mentionnez `@openhands` dans les commentaires pour :
- Poser des questions
- Demander des mises à jour
- Obtenir des explications de code

OpenHands va :
1. Commenter pour vous faire savoir qu'il y travaille
2. Effectuer la tâche demandée

#### Exemples de Commandes pour les Pull/Merge Requests

Voici quelques exemples de commandes que vous pouvez utiliser avec les pull/merge requests :

```
@openhands reflétez les commentaires de la revue
```

```
@openhands corrigez les conflits de fusion et assurez-vous que le CI passe
```
