# Résolveur de Problèmes Cloud

Le Résolveur de Problèmes Cloud automatise les corrections de code et fournit une assistance intelligente pour vos dépôts sur GitHub et GitLab.

## Configuration

Le Résolveur de Problèmes Cloud est disponible automatiquement lorsque vous accordez l'accès au dépôt OpenHands Cloud :
- [Accès au dépôt GitHub](./github-installation#adding-repository-access)
- [Accès au dépôt GitLab](./gitlab-installation#adding-repository-access)

## Utilisation

Après avoir accordé l'accès au dépôt OpenHands Cloud, vous pouvez utiliser le Résolveur de Problèmes Cloud sur les problèmes et les pull/merge requests dans vos dépôts.

### Travailler avec les Problèmes

Sur votre dépôt, étiquetez un problème avec `openhands`. OpenHands va :
1. Commenter le problème pour vous faire savoir qu'il y travaille
   - Vous pouvez cliquer sur le lien pour suivre la progression sur OpenHands Cloud
2. Ouvrir une pull request (GitHub) ou une merge request (GitLab) s'il détermine que le problème a été résolu avec succès
3. Commenter le problème avec un résumé des tâches effectuées et un lien vers la PR/MR

### Travailler avec les Pull/Merge Requests

Pour qu'OpenHands travaille sur les pull requests (GitHub) ou les merge requests (GitLab), mentionnez `@openhands` dans les commentaires pour :
- Poser des questions
- Demander des mises à jour
- Obtenir des explications de code

OpenHands va :
1. Commenter pour vous faire savoir qu'il y travaille
2. Effectuer la tâche demandée
