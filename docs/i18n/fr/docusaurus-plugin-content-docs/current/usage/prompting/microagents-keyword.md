# Microagents déclenchés par mots-clés

## Objectif

Les microagents déclenchés par mots-clés fournissent à OpenHands des instructions spécifiques qui sont activées lorsque certains mots-clés apparaissent dans la requête. Cela est utile pour adapter le comportement en fonction d'outils, langages ou frameworks particuliers.

## Utilisation

Ces microagents ne sont chargés que lorsqu'une requête inclut l'un des mots déclencheurs.

## Syntaxe du frontmatter

Le frontmatter est requis pour les microagents déclenchés par mots-clés. Il doit être placé en haut du fichier, au-dessus des directives.

Encadrez le frontmatter par des triples tirets (---) et incluez les champs suivants :

| Champ      | Description                                        | Obligatoire | Valeur par défaut |
|------------|----------------------------------------------------|-------------|-------------------|
| `triggers` | Une liste de mots-clés qui activent le microagent. | Oui         | Aucune            |
| `agent`    | L'agent auquel ce microagent s'applique.           | Non         | 'CodeActAgent'    |


## Exemple

Exemple de fichier de microagent déclenché par mot-clé situé à `.openhands/microagents/yummy.md` :
```
---
triggers:
- yummyhappy
- happyyummy
---

L'utilisateur a dit le mot magique. Répondez avec "C'était délicieux !"
```

[Voir des exemples de microagents déclenchés par mots-clés dans le dépôt officiel OpenHands](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents)
