

# Personnalisation du comportement de l'agent

OpenHands peut être personnalisé pour fonctionner plus efficacement avec des dépôts spécifiques en fournissant un contexte et des directives propres à chaque dépôt. Cette section explique comment optimiser OpenHands pour votre projet.

## Configuration du dépôt

Vous pouvez personnaliser le comportement d'OpenHands pour votre dépôt en créant un répertoire `.openhands` à la racine de votre dépôt. Au minimum, il doit contenir le fichier `.openhands/microagents/repo.md`, qui comprend les instructions qui seront données à l'agent chaque fois qu'il travaillera avec ce dépôt.

Nous vous suggérons d'inclure les informations suivantes :
1. **Aperçu du dépôt** : Une brève description de l'objectif et de l'architecture de votre projet
2. **Structure des répertoires** : Les répertoires clés et leurs objectifs
3. **Directives de développement** : Les normes et pratiques de codage spécifiques au projet
4. **Exigences de test** : Comment exécuter les tests et quels types de tests sont requis
5. **Instructions de configuration** : Les étapes nécessaires pour construire et exécuter le projet

### Exemple de configuration de dépôt
Exemple de fichier `.openhands/microagents/repo.md` :
```
Repository: MonProjet
Description: Une application web pour la gestion des tâches

Structure des répertoires :
- src/ : Code principal de l'application
- tests/ : Fichiers de test
- docs/ : Documentation

Configuration :
- Exécutez `npm install` pour installer les dépendances
- Utilisez `npm run dev` pour le développement
- Exécutez `npm test` pour les tests

Directives :
- Suivez la configuration ESLint
- Écrivez des tests pour toutes les nouvelles fonctionnalités
- Utilisez TypeScript pour le nouveau code
```

### Personnalisation des prompts

Lorsque vous travaillez avec un dépôt personnalisé :

1. **Référencez les normes du projet** : Mentionnez les normes ou les modèles de codage spécifiques utilisés dans votre projet
2. **Incluez le contexte** : Faites référence à la documentation pertinente ou aux implémentations existantes
3. **Spécifiez les exigences de test** : Incluez les exigences de test spécifiques au projet dans vos prompts

Exemple de prompt personnalisé :
```
Ajoutez une nouvelle fonctionnalité d'achèvement des tâches à src/components/TaskList.tsx en suivant nos modèles de composants existants.
Incluez des tests unitaires dans tests/components/ et mettez à jour la documentation dans docs/features/.
Le composant doit utiliser notre style partagé de src/styles/components.
```

### Meilleures pratiques pour la personnalisation du dépôt

1. **Gardez les instructions à jour** : Mettez régulièrement à jour votre répertoire `.openhands` au fur et à mesure de l'évolution de votre projet
2. **Soyez spécifique** : Incluez des chemins, des modèles et des exigences spécifiques à votre projet
3. **Documentez les dépendances** : Énumérez tous les outils et dépendances nécessaires au développement
4. **Incluez des exemples** : Fournissez des exemples de bons modèles de code de votre projet
5. **Spécifiez les conventions** : Documentez les conventions de nommage, l'organisation des fichiers et les préférences de style de code

En personnalisant OpenHands pour votre dépôt, vous obtiendrez des résultats plus précis et cohérents qui s'alignent sur les normes et les exigences de votre projet.

## Autres microagents
Vous pouvez créer d'autres instructions dans le répertoire `.openhands/microagents/` qui seront envoyées à l'agent si un mot-clé particulier est trouvé, comme `test`, `frontend` ou `migration`. Voir [Microagents](microagents.md) pour plus d'informations.
