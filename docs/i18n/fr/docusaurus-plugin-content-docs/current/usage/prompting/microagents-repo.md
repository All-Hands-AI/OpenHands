# Microagents Généraux de Dépôt

## Objectif

Directives générales pour qu'OpenHands travaille plus efficacement avec le dépôt.

## Utilisation

Ces microagents sont toujours chargés dans le contexte.

## Syntaxe du Frontmatter

Le frontmatter pour ce type de microagent est facultatif.

Le frontmatter doit être encadré par des triples tirets (---) et peut inclure les champs suivants :

| Champ      | Description                             | Obligatoire | Valeur par défaut |
|------------|-----------------------------------------|-------------|-------------------|
| `agent`    | L'agent auquel ce microagent s'applique | Non         | 'CodeActAgent'    |

## Exemple

Exemple de fichier microagent général de dépôt situé à `.openhands/microagents/repo.md` :
```
Ce projet est une application TODO qui permet aux utilisateurs de suivre des éléments TODO.

Pour la configurer, vous pouvez exécuter `npm run build`.
Assurez-vous toujours que les tests sont réussis avant de valider les modifications. Vous pouvez exécuter les tests en lançant `npm run test`.
```

[Voir plus d'exemples de microagents généraux de dépôt ici.](https://github.com/All-Hands-AI/OpenHands/tree/main/.openhands/microagents)
