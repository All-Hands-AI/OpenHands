---
sidebar_position: 9
---

# Aperçu du développement

Ce guide fournit un aperçu des principales ressources de documentation disponibles dans le dépôt OpenHands. Que vous souhaitiez contribuer, comprendre l'architecture ou travailler sur des composants spécifiques, ces ressources vous aideront à naviguer efficacement dans le code.

## Documentation principale

### Fondamentaux du projet
- **Aperçu principal du projet** (`/README.md`)
  Le point d'entrée principal pour comprendre OpenHands, y compris les fonctionnalités et les instructions de configuration de base.

- **Guide de développement** (`/Development.md`)
  Guide complet pour les développeurs travaillant sur OpenHands, incluant la configuration, les exigences et les flux de travail de développement.

- **Directives de contribution** (`/CONTRIBUTING.md`)
  Informations essentielles pour les contributeurs, couvrant le style de code, le processus de PR et les flux de travail de contribution.

### Documentation des composants

#### Frontend
- **Application Frontend** (`/frontend/README.md`)
  Guide complet pour configurer et développer l'application frontend basée sur React.

#### Backend
- **Implémentation Backend** (`/openhands/README.md`)
  Documentation détaillée de l'implémentation et de l'architecture du backend Python.

- **Documentation du serveur** (`/openhands/server/README.md`)
  Détails d'implémentation du serveur, documentation API et architecture des services.

- **Environnement d'exécution** (`/openhands/runtime/README.md`)
  Documentation couvrant l'environnement d'exécution, le modèle d'exécution et les configurations d'exécution.

#### Infrastructure
- **Documentation des conteneurs** (`/containers/README.md`)
  Informations complètes sur les conteneurs Docker, les stratégies de déploiement et la gestion des conteneurs.

### Tests et évaluation
- **Guide des tests unitaires** (`/tests/unit/README.md`)
  Instructions pour écrire, exécuter et maintenir les tests unitaires.

- **Cadre d'évaluation** (`/evaluation/README.md`)
  Documentation du cadre d'évaluation, des benchmarks et des tests de performance.

### Fonctionnalités avancées
- **Architecture des microagents** (`/microagents/README.md`)
  Informations détaillées sur l'architecture des microagents, leur implémentation et leur utilisation.

### Normes de documentation
- **Guide de style de documentation** (`/docs/DOC_STYLE_GUIDE.md`)
  Normes et directives pour la rédaction et la maintenance de la documentation du projet.

## Débuter avec le développement

Si vous débutez dans le développement avec OpenHands, nous vous recommandons de suivre cette séquence :

1. Commencez par le `README.md` principal pour comprendre l'objectif et les fonctionnalités du projet
2. Consultez les directives de `CONTRIBUTING.md` si vous prévoyez de contribuer
3. Suivez les instructions de configuration dans `Development.md`
4. Plongez dans la documentation spécifique des composants selon votre domaine d'intérêt :
   - Les développeurs frontend devraient se concentrer sur `/frontend/README.md`
   - Les développeurs backend devraient commencer par `/openhands/README.md`
   - Le travail d'infrastructure devrait commencer par `/containers/README.md`

## Mises à jour de la documentation

Lorsque vous apportez des modifications au code, veuillez vous assurer que :
1. La documentation pertinente est mise à jour pour refléter vos changements
2. Les nouvelles fonctionnalités sont documentées dans les fichiers README appropriés
3. Tout changement d'API est reflété dans la documentation du serveur
4. La documentation suit le guide de style dans `/docs/DOC_STYLE_GUIDE.md`
