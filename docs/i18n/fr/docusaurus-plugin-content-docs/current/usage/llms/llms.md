# 🤖 Backends LLM

:::note
Cette section est destinée aux utilisateurs qui souhaitent connecter OpenHands à différents LLMs.
:::

OpenHands peut se connecter à n'importe quel LLM pris en charge par LiteLLM. Cependant, il nécessite un modèle puissant pour fonctionner.

## Recommandations de modèles

Sur la base de nos évaluations des modèles de langage pour les tâches de programmation (utilisant le jeu de données SWE-bench), nous pouvons fournir quelques
recommandations pour la sélection de modèles. Nos derniers résultats d'évaluation peuvent être consultés dans [ce tableur](https://docs.google.com/spreadsheets/d/1wOUdFCMyY6Nt0AIqF705KN4JKOWgeI4wUGUP60krXXs/edit?gid=0).

Sur la base de ces résultats et des retours de la communauté, les modèles suivants ont été vérifiés comme fonctionnant raisonnablement bien avec OpenHands :

- [anthropic/claude-3-7-sonnet-20250219](https://www.anthropic.com/api) (recommandé)
- [gemini/gemini-2.5-pro](https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/)
- [deepseek/deepseek-chat](https://api-docs.deepseek.com/)
- [openai/o3-mini](https://openai.com/index/openai-o3-mini/)
- [openai/o3](https://openai.com/index/introducing-o3-and-o4-mini/)
- [openai/o4-mini](https://openai.com/index/introducing-o3-and-o4-mini/)
- [all-hands/openhands-lm-32b-v0.1](https://www.all-hands.dev/blog/introducing-openhands-lm-32b----a-strong-open-coding-agent-model) -- disponible via [OpenRouter](https://openrouter.ai/all-hands/openhands-lm-32b-v0.1)


:::warning
OpenHands enverra de nombreuses requêtes au LLM que vous configurez. La plupart de ces LLMs ont un coût, alors assurez-vous de définir des limites de dépenses et de surveiller l'utilisation.
:::

Si vous avez réussi à exécuter OpenHands avec des LLMs spécifiques qui ne figurent pas dans la liste, veuillez les ajouter à la liste vérifiée. Nous
vous encourageons également à ouvrir une PR pour partager votre processus de configuration afin d'aider d'autres utilisateurs du même fournisseur et LLM !

Pour une liste complète des fournisseurs et modèles disponibles, veuillez consulter la
[documentation litellm](https://docs.litellm.ai/docs/providers).

:::note
La plupart des modèles locaux et open source actuels ne sont pas aussi puissants. Lorsque vous utilisez de tels modèles, vous pourriez constater de longs
temps d'attente entre les messages, des réponses médiocres ou des erreurs concernant un JSON mal formé. OpenHands ne peut être que aussi puissant que les
modèles qui l'alimentent. Cependant, si vous en trouvez qui fonctionnent, veuillez les ajouter à la liste vérifiée ci-dessus.
:::

## Configuration LLM

Les éléments suivants peuvent être définis dans l'interface utilisateur d'OpenHands via les Paramètres :

- `Fournisseur LLM`
- `Modèle LLM`
- `Clé API`
- `URL de base` (via les paramètres `Avancés`)

Il existe certains paramètres qui peuvent être nécessaires pour certains LLMs/fournisseurs qui ne peuvent pas être définis via l'interface utilisateur. Au lieu de cela, ils
peuvent être définis via des variables d'environnement transmises à la commande docker run lors du démarrage de l'application
en utilisant `-e` :

- `LLM_API_VERSION`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_DROP_PARAMS`
- `LLM_DISABLE_VISION`
- `LLM_CACHING_PROMPT`

Nous avons quelques guides pour exécuter OpenHands avec des fournisseurs de modèles spécifiques :

- [Azure](llms/azure-llms)
- [Google](llms/google-llms)
- [Groq](llms/groq)
- [LLMs locaux avec SGLang ou vLLM](llms/../local-llms.md)
- [Proxy LiteLLM](llms/litellm-proxy)
- [OpenAI](llms/openai-llms)
- [OpenRouter](llms/openrouter)

### Nouvelles tentatives d'API et limites de taux

Les fournisseurs de LLM ont généralement des limites de taux, parfois très basses, et peuvent nécessiter des nouvelles tentatives. OpenHands réessaiera automatiquement
les requêtes s'il reçoit une erreur de limite de taux (code d'erreur 429).

Vous pouvez personnaliser ces options selon vos besoins pour le fournisseur que vous utilisez. Consultez leur documentation et définissez les
variables d'environnement suivantes pour contrôler le nombre de nouvelles tentatives et le temps entre les tentatives :

- `LLM_NUM_RETRIES` (Par défaut 4 fois)
- `LLM_RETRY_MIN_WAIT` (Par défaut 5 secondes)
- `LLM_RETRY_MAX_WAIT` (Par défaut 30 secondes)
- `LLM_RETRY_MULTIPLIER` (Par défaut 2)

Si vous exécutez OpenHands en mode développement, vous pouvez également définir ces options dans le fichier `config.toml` :

```toml
[llm]
num_retries = 4
retry_min_wait = 5
retry_max_wait = 30
retry_multiplier = 2
```
