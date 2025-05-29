# Installation GitHub

Ce guide vous accompagne dans le processus d'installation et de configuration d'OpenHands Cloud pour vos dépôts GitHub.

## Prérequis

- Un compte GitHub
- Accès à OpenHands Cloud

## Étapes d'Installation

1. Connectez-vous à [OpenHands Cloud](https://app.all-hands.dev)
2. Si vous n'avez pas encore connecté votre compte GitHub :
   - Cliquez sur `Se connecter à GitHub`
   - Examinez et acceptez les conditions d'utilisation
   - Autorisez l'application OpenHands AI

## Ajout d'Accès au Dépôt

Vous pouvez accorder à OpenHands l'accès à des dépôts spécifiques :

1. Cliquez sur le menu déroulant `Sélectionner un projet GitHub`, puis sélectionnez `Ajouter plus de dépôts...`
2. Sélectionnez votre organisation et choisissez les dépôts spécifiques auxquels vous souhaitez accorder l'accès à OpenHands.
   - OpenHands demande des jetons à courte durée de vie (expiration de 8 heures) avec ces permissions :
     - Actions : Lecture et écriture
     - Administration : Lecture seule
     - Statuts de commit : Lecture et écriture
     - Contenus : Lecture et écriture
     - Problèmes : Lecture et écriture
     - Métadonnées : Lecture seule
     - Pull requests : Lecture et écriture
     - Webhooks : Lecture et écriture
     - Workflows : Lecture et écriture
   - L'accès au dépôt pour un utilisateur est accordé en fonction de :
     - Permission accordée pour le dépôt
     - Permissions GitHub de l'utilisateur (propriétaire/collaborateur)
3. Cliquez sur `Installer & Autoriser`

![Ajout de l'accès au dépôt à OpenHands](/img/cloud/add-repo.png)

## Modification de l'Accès au Dépôt

Vous pouvez modifier l'accès au dépôt à tout moment :
* En utilisant le même workflow `Sélectionner un projet GitHub > Ajouter plus de dépôts`, ou
* En visitant la page Paramètres et en sélectionnant `Configurer les Dépôts GitHub` dans la section `Paramètres GitHub`.

## Utilisation d'OpenHands avec GitHub

Une fois que vous avez accordé l'accès au dépôt, vous pouvez utiliser OpenHands avec vos dépôts GitHub.

Pour plus de détails sur l'utilisation d'OpenHands avec les problèmes et les pull requests GitHub, consultez la documentation du [Résolveur de Problèmes Cloud](./cloud-issue-resolver.md).

## Prochaines Étapes

- [Accéder à l'Interface Cloud](./cloud-ui.md) pour interagir avec l'interface web
- [Utiliser le Résolveur de Problèmes Cloud](./cloud-issue-resolver.md) pour automatiser les corrections de code et obtenir de l'aide
- [Utiliser l'API Cloud](./cloud-api.md) pour interagir programmatiquement avec OpenHands
