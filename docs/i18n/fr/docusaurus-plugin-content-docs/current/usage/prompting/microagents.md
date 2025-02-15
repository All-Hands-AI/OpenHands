

# Micro-Agents

OpenHands utilise des micro-agents spécialisés pour gérer efficacement des tâches et des contextes spécifiques. Ces micro-agents sont de petits composants ciblés qui fournissent un comportement et des connaissances spécialisés pour des scénarios particuliers.

## Aperçu

Les micro-agents sont définis dans des fichiers markdown sous le répertoire `openhands/agenthub/codeact_agent/micro/`. Chaque micro-agent est configuré avec :

- Un nom unique
- Le type d'agent (généralement CodeActAgent)
- Des mots-clés déclencheurs qui activent l'agent
- Des instructions et des capacités spécifiques

## Micro-Agents Disponibles

### Agent GitHub
**Fichier** : `github.md`
**Déclencheurs** : `github`, `git`

L'agent GitHub se spécialise dans les interactions avec l'API GitHub et la gestion des dépôts. Il :
- A accès à un `GITHUB_TOKEN` pour l'authentification API
- Suit des directives strictes pour les interactions avec les dépôts
- Gère les branches et les pull requests
- Utilise l'API GitHub au lieu des interactions avec le navigateur web

Fonctionnalités clés :
- Protection des branches (empêche les push directs vers main/master)
- Création automatisée de PR
- Gestion de la configuration Git
- Approche API-first pour les opérations GitHub

### Agent NPM
**Fichier** : `npm.md`
**Déclencheurs** : `npm`

Se spécialise dans la gestion des packages npm avec un focus spécifique sur :
- Les opérations shell non interactives
- La gestion automatisée des confirmations en utilisant la commande Unix 'yes'
- L'automatisation de l'installation des packages

### Micro-Agents Personnalisés

Vous pouvez créer vos propres micro-agents en ajoutant de nouveaux fichiers markdown dans le répertoire des micro-agents. Chaque fichier doit suivre cette structure :

```markdown
---
name: nom_de_l_agent
agent: CodeActAgent
triggers:
- mot_declencheur1
- mot_declencheur2
---

Instructions et capacités pour le micro-agent...
```

## Bonnes Pratiques

Lorsque vous travaillez avec des micro-agents :

1. **Utilisez les déclencheurs appropriés** : Assurez-vous que vos commandes incluent les mots-clés déclencheurs pertinents pour activer le bon micro-agent
2. **Suivez les directives de l'agent** : Chaque agent a des instructions et des limitations spécifiques - respectez-les pour des résultats optimaux
3. **Approche API-First** : Lorsque c'est possible, utilisez les endpoints d'API plutôt que les interfaces web
4. **Automatisation conviviale** : Concevez des commandes qui fonctionnent bien dans des environnements non interactifs

## Intégration

Les micro-agents sont automatiquement intégrés dans le workflow d'OpenHands. Ils :
- Surveillent les commandes entrantes pour détecter leurs mots-clés déclencheurs
- S'activent lorsque des déclencheurs pertinents sont détectés
- Appliquent leurs connaissances et capacités spécialisées
- Suivent leurs directives et restrictions spécifiques

## Exemple d'utilisation

```bash
# Exemple d'agent GitHub
git checkout -b feature-branch
git commit -m "Add new feature"
git push origin feature-branch

# Exemple d'agent NPM
yes | npm install package-name
```

Pour plus d'informations sur des agents spécifiques, reportez-vous à leurs fichiers de documentation individuels dans le répertoire des micro-agents.

## Contribuer un Micro-Agent

Pour contribuer un nouveau micro-agent à OpenHands, suivez ces directives :

### 1. Planification de votre Micro-Agent

Avant de créer un micro-agent, considérez :
- Quel problème ou cas d'utilisation spécifique va-t-il adresser ?
- Quelles capacités ou connaissances uniques devrait-il avoir ?
- Quels mots-clés déclencheurs ont du sens pour l'activer ?
- Quelles contraintes ou directives devrait-il suivre ?

### 2. Structure du fichier

Créez un nouveau fichier markdown dans `openhands/agenthub/codeact_agent/micro/` avec un nom descriptif (par ex., `docker.md` pour un agent axé sur Docker).

### 3. Composants requis

Votre fichier de micro-agent doit inclure :

1. **Front Matter** : Métadonnées YAML au début du fichier :
```markdown
---
name: nom_de_votre_agent
agent: CodeActAgent
triggers:
- mot_declencheur1
- mot_declencheur2
---
```

2. **Instructions** : Directives claires et spécifiques pour le comportement de l'agent :
```markdown
Vous êtes responsable de [tâche/domaine spécifique].

Responsabilités clés :
1. [Responsabilité 1]
2. [Responsabilité 2]

Directives :
- [Directive 1]
- [Directive 2]

Exemples d'utilisation :
[Exemple 1]
[Exemple 2]
```

### 4. Bonnes pratiques pour le développement de Micro-Agents

1. **Portée claire** : Gardez l'agent concentré sur un domaine ou une tâche spécifique
2. **Instructions explicites** : Fournissez des directives claires et sans ambiguïté
3. **Exemples utiles** : Incluez des exemples pratiques de cas d'utilisation courants
4. **Sécurité d'abord** : Incluez les avertissements et contraintes nécessaires
5. **Conscience de l'intégration** : Considérez comment l'agent interagit avec les autres composants

### 5. Tester votre Micro-Agent

Avant de soumettre :
1. Testez l'agent avec divers prompts
2. Vérifiez que les mots-clés déclencheurs activent correctement l'agent
3. Assurez-vous que les instructions sont claires et complètes
4. Vérifiez les conflits potentiels avec les agents existants

### 6. Exemple d'implémentation

Voici un modèle pour un nouveau micro-agent :

```markdown
---
name: docker
agent: CodeActAgent
triggers:
- docker
- conteneur
---

Vous êtes responsable de la gestion des conteneurs Docker et de la création de Dockerfiles.

Responsabilités clés :
1. Créer et modifier des Dockerfiles
2. Gérer le cycle de vie des conteneurs
3. Gérer les configurations Docker Compose

Directives :
- Utilisez toujours des images de base officielles lorsque possible
- Incluez les considérations de sécurité nécessaires
- Suivez les bonnes pratiques Docker pour l'optimisation des couches

Exemples :
1. Créer un Dockerfile :
   ```dockerfile
   FROM node:18-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   CMD ["npm", "start"]
   ```

2. Utilisation de Docker Compose :
   ```yaml
   version: '3'
   services:
     web:
       build: .
       ports:
         - "3000:3000"
   ```

N'oubliez pas de :
- Valider la syntaxe du Dockerfile
- Vérifier les vulnérabilités de sécurité
- Optimiser le temps de build et la taille de l'image
```

### 7. Processus de soumission

1. Créez votre fichier de micro-agent dans le bon répertoire
2. Testez minutieusement
3. Soumettez une pull request avec :
   - Le nouveau fichier de micro-agent
   - La documentation mise à jour si nécessaire
   - La description du but et des capacités de l'agent

N'oubliez pas que les micro-agents sont un moyen puissant d'étendre les capacités d'OpenHands dans des domaines spécifiques. Des agents bien conçus peuvent améliorer significativement la capacité du système à gérer des tâches spécialisées.
