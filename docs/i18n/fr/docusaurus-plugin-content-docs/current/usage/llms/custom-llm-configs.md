# Configurations LLM personnalisées

OpenHands permet de définir plusieurs configurations LLM nommées dans votre fichier `config.toml`. Cette fonctionnalité vous permet d'utiliser différentes configurations LLM pour différents usages, comme utiliser un modèle moins coûteux pour les tâches qui ne nécessitent pas de réponses de haute qualité, ou utiliser différents modèles avec différents paramètres pour des agents spécifiques.

## Comment ça fonctionne

Les configurations LLM nommées sont définies dans le fichier `config.toml` en utilisant des sections qui commencent par `llm.`. Par exemple :

```toml
# Configuration LLM par défaut
[llm]
model = "gpt-4"
api_key = "votre-clé-api"
temperature = 0.0

# Configuration LLM personnalisée pour un modèle moins coûteux
[llm.gpt3]
model = "gpt-3.5-turbo"
api_key = "votre-clé-api"
temperature = 0.2

# Une autre configuration personnalisée avec des paramètres différents
[llm.haute-creativite]
model = "gpt-4"
api_key = "votre-clé-api"
temperature = 0.8
top_p = 0.9
```

Chaque configuration nommée hérite de tous les paramètres de la section `[llm]` par défaut et peut remplacer n'importe lequel de ces paramètres. Vous pouvez définir autant de configurations personnalisées que nécessaire.

## Utilisation des configurations personnalisées

### Avec les agents

Vous pouvez spécifier quelle configuration LLM un agent doit utiliser en définissant le paramètre `llm_config` dans la section de configuration de l'agent :

```toml
[agent.RepoExplorerAgent]
# Utiliser la configuration GPT-3 moins coûteuse pour cet agent
llm_config = 'gpt3'

[agent.CodeWriterAgent]
# Utiliser la configuration haute créativité pour cet agent
llm_config = 'haute-creativite'
```

### Options de configuration

Chaque configuration LLM nommée prend en charge toutes les mêmes options que la configuration LLM par défaut. Celles-ci incluent :

- Sélection du modèle (`model`)
- Configuration de l'API (`api_key`, `base_url`, etc.)
- Paramètres du modèle (`temperature`, `top_p`, etc.)
- Paramètres de nouvelle tentative (`num_retries`, `retry_multiplier`, etc.)
- Limites de jetons (`max_input_tokens`, `max_output_tokens`)
- Et toutes les autres options de configuration LLM

Pour une liste complète des options disponibles, consultez la section Configuration LLM dans la documentation des [Options de configuration](../configuration-options).

## Cas d'utilisation

Les configurations LLM personnalisées sont particulièrement utiles dans plusieurs scénarios :

- **Optimisation des coûts** : Utiliser des modèles moins coûteux pour les tâches qui ne nécessitent pas de réponses de haute qualité, comme l'exploration de dépôt ou les opérations simples sur les fichiers.
- **Réglage spécifique aux tâches** : Configurer différentes valeurs de température et de top_p pour les tâches qui nécessitent différents niveaux de créativité ou de déterminisme.
- **Différents fournisseurs** : Utiliser différents fournisseurs LLM ou points d'accès API pour différentes tâches.
- **Tests et développement** : Basculer facilement entre différentes configurations de modèles pendant le développement et les tests.

## Exemple : Optimisation des coûts

Un exemple pratique d'utilisation des configurations LLM personnalisées pour optimiser les coûts :

```toml
# Configuration par défaut utilisant GPT-4 pour des réponses de haute qualité
[llm]
model = "gpt-4"
api_key = "votre-clé-api"
temperature = 0.0

# Configuration moins coûteuse pour l'exploration de dépôt
[llm.repo-explorer]
model = "gpt-3.5-turbo"
temperature = 0.2

# Configuration pour la génération de code
[llm.code-gen]
model = "gpt-4"
temperature = 0.0
max_output_tokens = 2000

[agent.RepoExplorerAgent]
llm_config = 'repo-explorer'

[agent.CodeWriterAgent]
llm_config = 'code-gen'
```

Dans cet exemple :
- L'exploration de dépôt utilise un modèle moins coûteux car il s'agit principalement de comprendre et de naviguer dans le code
- La génération de code utilise GPT-4 avec une limite de jetons plus élevée pour générer des blocs de code plus importants
- La configuration par défaut reste disponible pour les autres tâches

:::note
Les configurations LLM personnalisées ne sont disponibles que lors de l'utilisation d'OpenHands en mode développement, via `main.py` ou `cli.py`. Lors de l'exécution via `docker run`, veuillez utiliser les options de configuration standard.
:::
