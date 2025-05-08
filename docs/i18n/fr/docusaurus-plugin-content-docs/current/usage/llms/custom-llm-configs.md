# Configurations LLM personnalisées

OpenHands permet de définir plusieurs configurations LLM nommées dans votre fichier `config.toml`. Cette fonctionnalité vous permet d'utiliser différentes configurations LLM pour différents usages, comme utiliser un modèle moins coûteux pour des tâches qui ne nécessitent pas de réponses de haute qualité, ou utiliser différents modèles avec différents paramètres pour des agents spécifiques.

## Comment ça fonctionne

Les configurations LLM nommées sont définies dans le fichier `config.toml` en utilisant des sections qui commencent par `llm.`. Par exemple :

```toml
# Configuration LLM par défaut
[llm]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.0

# Configuration LLM personnalisée pour un modèle moins cher
[llm.gpt3]
model = "gpt-3.5-turbo"
api_key = "your-api-key"
temperature = 0.2

# Une autre configuration personnalisée avec différents paramètres
[llm.high-creativity]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.8
top_p = 0.9
```

Chaque configuration nommée hérite de tous les paramètres de la section `[llm]` par défaut et peut remplacer n'importe lequel de ces paramètres. Vous pouvez définir autant de configurations personnalisées que nécessaire.

## Utilisation des configurations personnalisées

### Avec les agents

Vous pouvez spécifier quelle configuration LLM un agent doit utiliser en définissant le paramètre `llm_config` dans la section de configuration de l'agent :

```toml
[agent.RepoExplorerAgent]
# Utiliser la configuration GPT-3 moins chère pour cet agent
llm_config = 'gpt3'

[agent.CodeWriterAgent]
# Utiliser la configuration haute créativité pour cet agent
llm_config = 'high-creativity'
```

### Options de configuration

Chaque configuration LLM nommée prend en charge toutes les mêmes options que la configuration LLM par défaut. Celles-ci incluent :

- Sélection du modèle (`model`)
- Configuration de l'API (`api_key`, `base_url`, etc.)
- Paramètres du modèle (`temperature`, `top_p`, etc.)
- Paramètres de nouvelle tentative (`num_retries`, `retry_multiplier`, etc.)
- Limites de tokens (`max_input_tokens`, `max_output_tokens`)
- Et toutes les autres options de configuration LLM

Pour une liste complète des options disponibles, consultez la section Configuration LLM dans la documentation [Options de configuration](../configuration-options).

## Cas d'utilisation

Les configurations LLM personnalisées sont particulièrement utiles dans plusieurs scénarios :

- **Optimisation des coûts** : Utilisez des modèles moins chers pour des tâches qui ne nécessitent pas de réponses de haute qualité, comme l'exploration de dépôts ou les opérations simples sur les fichiers.
- **Réglage spécifique aux tâches** : Configurez différentes valeurs de température et de top_p pour des tâches qui nécessitent différents niveaux de créativité ou de déterminisme.
- **Différents fournisseurs** : Utilisez différents fournisseurs LLM ou points d'accès API pour différentes tâches.
- **Tests et développement** : Passez facilement d'une configuration de modèle à une autre pendant le développement et les tests.

## Exemple : Optimisation des coûts

Un exemple pratique d'utilisation de configurations LLM personnalisées pour optimiser les coûts :

```toml
# Configuration par défaut utilisant GPT-4 pour des réponses de haute qualité
[llm]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.0

# Configuration moins chère pour l'exploration de dépôts
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
- L'exploration de dépôts utilise un modèle moins cher puisqu'il s'agit principalement de comprendre et de naviguer dans le code
- La génération de code utilise GPT-4 avec une limite de tokens plus élevée pour générer des blocs de code plus grands
- La configuration par défaut reste disponible pour d'autres tâches

# Configurations personnalisées avec des noms réservés

OpenHands peut utiliser des configurations LLM personnalisées nommées avec des noms réservés, pour des cas d'utilisation spécifiques. Si vous spécifiez le modèle et d'autres paramètres sous les noms réservés, OpenHands les chargera et les utilisera pour un objectif spécifique. À ce jour, une telle configuration est implémentée : l'éditeur de brouillon.

## Configuration de l'éditeur de brouillon

La configuration `draft_editor` est un groupe de paramètres que vous pouvez fournir pour spécifier le modèle à utiliser pour l'ébauche préliminaire des modifications de code, pour toutes les tâches qui impliquent l'édition et le raffinement du code. Vous devez la fournir sous la section `[llm.draft_editor]`.

Par exemple, vous pouvez définir dans `config.toml` un éditeur de brouillon comme ceci :

```toml
[llm.draft_editor]
model = "gpt-4"
temperature = 0.2
top_p = 0.95
presence_penalty = 0.0
frequency_penalty = 0.0
```

Cette configuration :
- Utilise GPT-4 pour des modifications et suggestions de haute qualité
- Définit une température basse (0,2) pour maintenir la cohérence tout en permettant une certaine flexibilité
- Utilise une valeur top_p élevée (0,95) pour considérer un large éventail d'options de tokens
- Désactive les pénalités de présence et de fréquence pour maintenir l'accent sur les modifications spécifiques nécessaires

Utilisez cette configuration lorsque vous souhaitez qu'un LLM ébauche des modifications avant de les effectuer. En général, cela peut être utile pour :
- Examiner et suggérer des améliorations de code
- Affiner le contenu existant tout en conservant son sens fondamental
- Apporter des modifications précises et ciblées au code ou au texte

:::note
Les configurations LLM personnalisées ne sont disponibles que lorsque vous utilisez OpenHands en mode développement, via `main.py` ou `cli.py`. Lors de l'exécution via `docker run`, veuillez utiliser les options de configuration standard.
:::
