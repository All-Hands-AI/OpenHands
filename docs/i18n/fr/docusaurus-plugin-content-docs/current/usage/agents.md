---
sidebar_position: 3
---

# 🧠 Agents et Capacités

## Agent CodeAct

### Description

Cet agent implémente l'idée CodeAct ([article](https://arxiv.org/abs/2402.01030), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) qui consolide les **act**ions des agents LLM en un espace d'action **code** unifié pour à la fois la _simplicité_ et la _performance_ (voir article pour plus de détails).

L'idée conceptuelle est illustrée ci-dessous. À chaque tour, l'agent peut :

1. **Converse** : Communiquer avec les humains en langage naturel pour demander des clarifications, des confirmations, etc.
2. **CodeAct** : Choisir d'accomplir la tâche en exécutant du code

- Exécuter toute commande `bash` Linux valide
- Exécuter tout code `Python` valide avec [un interpréteur Python interactif](https://ipython.org/). Cela est simulé à travers la commande `bash`, voir le système de plugin ci-dessous pour plus de détails.

![image](https://github.com/OpenDevin/OpenDevin/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

### Système de Plugin

Pour rendre l'agent CodeAct plus puissant avec seulement l'accès à l'espace d'action `bash`, l'agent CodeAct exploite le système de plugins d'OpenDevin:

- [Plugin Jupyter](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/jupyter) : pour l'exécution d'IPython via la commande bash
- [Plugin outil agent SWE](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/swe_agent_commands) : Outils de ligne de commande bash puissants pour les tâches de développement logiciel introduits par [swe-agent](https://github.com/princeton-nlp/swe-agent).

### Démonstration

https://github.com/OpenDevin/OpenDevin/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

_Exemple de CodeActAgent avec `gpt-4-turbo-2024-04-09` effectuant une tâche de science des données (régression linéaire)_

### Actions

`Action`,
`CmdRunAction`,
`IPythonRunCellAction`,
`AgentEchoAction`,
`AgentFinishAction`,
`AgentTalkAction`

### Observations

`CmdOutputObservation`,
`IPythonRunCellObservation`,
`AgentMessageObservation`,
`UserMessageObservation`

### Méthodes

| Méthode          | Description                                                                                                                                     |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__`       | Initialise un agent avec `llm` et une liste de messages `list[Mapping[str, str]]`                                                                |
| `step`           | Effectue une étape en utilisant l'agent CodeAct. Cela inclut la collecte d'informations sur les étapes précédentes et invite le modèle à exécuter une commande. |
| `search_memory`  | Pas encore implémenté                                                                                                                             |

### En cours de réalisation & prochaine étape

[] Support de la navigation sur le web
[] Compléter le workflow pour l'agent CodeAct afin de soumettre des PRs Github

## Agent Monologue

### Description

L'agent Monologue utilise la mémoire à long terme et à court terme pour accomplir des tâches.
La mémoire à long terme est stockée en tant qu'objet LongTermMemory et le modèle l'utilise pour rechercher des exemples du passé.
La mémoire à court terme est stockée en tant qu'objet Monologue et le modèle peut la condenser si nécessaire.

### Actions

`Action`,
`NullAction`,
`CmdRunAction`,
`FileWriteAction`,
`FileReadAction`,
`AgentRecallAction`,
`BrowseURLAction`,
`GithubPushAction`,
`AgentThinkAction`

### Observations

`Observation`,
`NullObservation`,
`CmdOutputObservation`,
`FileReadObservation`,
`AgentRecallObservation`,
`BrowserOutputObservation`

### Méthodes

| Méthode         | Description                                                                                                                                   |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__`      | Initialise l'agent avec une mémoire à long terme et un monologue interne                                                                      |
| `_add_event`    | Ajoute des événements au monologue de l'agent et condense avec un résumé automatiquement si le monologue est trop long                            |
| `_initialize`   | Utilise la liste `INITIAL_THOUGHTS` pour donner à l'agent un contexte pour ses capacités et comment naviguer dans le `/workspace`                    |
| `step`          | Modifie l'état actuel en ajoutant les actions et observations les plus récentes, puis invite le modèle à réfléchir à la prochaine action à entreprendre. |
| `search_memory` | Utilise `VectorIndexRetriever` pour trouver des souvenirs liés à la mémoire à long terme.                                                             |

## Agent Planificateur

### Description

L'agent planificateur utilise une stratégie d'incitation spéciale pour créer des plans à long terme pour résoudre les problèmes.
L'agent reçoit ses paires action-observation précédentes, la tâche actuelle, et un indice basé sur la dernière action effectuée à chaque étape.

### Actions

`NullAction`,
`CmdRunAction`,
`BrowseURLAction`,
`GithubPushAction`,
`FileReadAction`,
`FileWriteAction`,
`AgentRecallAction`,
`AgentThinkAction`,
`AgentFinishAction`,
`AgentSummarizeAction`,
`AddTaskAction`,
`ModifyTaskAction`,

### Observations

`Observation`,
`NullObservation`,
`CmdOutputObservation`,
`FileReadObservation`,
`AgentRecallObservation`,
`BrowserOutputObservation`

### Méthodes

| Méthode          | Description                                                                                                                                                                               |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__`       | Initialise un agent avec `llm`                                                                                                                                                           |
| `step`           | Vérifie si l'étape actuelle est terminée, retourne `AgentFinishAction` si oui. Sinon, crée une incitation de planification et l'envoie au modèle pour inférence, en ajoutant le résultat comme prochaine action. |
| `search_memory`  | Pas encore implémenté                                                                                                                                                                       |
