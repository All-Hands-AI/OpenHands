# Microagents globaux

## Aperçu

Les microagents globaux sont des [microagents déclenchés par mot-clé](./microagents-keyword) qui s'appliquent à tous les utilisateurs d'OpenHands. Une liste des microagents globaux actuels peut être trouvée [dans le dépôt OpenHands](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents).

## Contribuer un microagent global

Vous pouvez créer des microagents globaux et les partager avec la communauté en ouvrant une pull request sur le dépôt officiel.

Consultez le fichier [CONTRIBUTING.md](https://github.com/All-Hands-AI/OpenHands/blob/main/CONTRIBUTING.md) pour des instructions spécifiques sur la façon de contribuer à OpenHands.

### Bonnes pratiques pour les microagents globaux

- **Portée claire** : Gardez le microagent concentré sur un domaine ou une tâche spécifique.
- **Instructions explicites** : Fournissez des directives claires et sans ambiguïté.
- **Exemples utiles** : Incluez des exemples pratiques de cas d'utilisation courants.
- **Sécurité d'abord** : Incluez les avertissements et contraintes nécessaires.
- **Conscience d'intégration** : Tenez compte de la façon dont le microagent interagit avec d'autres composants.

### Étapes pour contribuer un microagent global

#### 1. Planifier le microagent global

Avant de créer un microagent global, considérez :

- Quel problème spécifique ou cas d'utilisation va-t-il traiter ?
- Quelles capacités ou connaissances uniques devrait-il avoir ?
- Quels mots déclencheurs ont du sens pour l'activer ?
- Quelles contraintes ou directives devrait-il suivre ?

#### 2. Créer le fichier

Créez un nouveau fichier Markdown avec un nom descriptif dans le répertoire approprié :
[`microagents/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents)

#### 3. Tester le microagent global

- Testez l'agent avec diverses requêtes.
- Vérifiez que les mots déclencheurs activent correctement l'agent.
- Assurez-vous que les instructions sont claires et complètes.
- Vérifiez les conflits potentiels et les chevauchements avec les agents existants.

#### 4. Processus de soumission

Soumettez une pull request avec :

- Le nouveau fichier de microagent.
- Documentation mise à jour si nécessaire.
- Description de l'objectif et des capacités de l'agent.
