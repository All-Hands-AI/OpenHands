

# OpenRouter

OpenHands utilise LiteLLM pour effectuer des appels aux modèles de chat sur OpenRouter. Vous pouvez trouver leur documentation sur l'utilisation d'OpenRouter en tant que fournisseur [ici](https://docs.litellm.ai/docs/providers/openrouter).

## Configuration

Lors de l'exécution d'OpenHands, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les paramètres :
* `LLM Provider` à `OpenRouter`
* `LLM Model` au modèle que vous utiliserez.
[Visitez ici pour voir une liste complète des modèles OpenRouter](https://openrouter.ai/models).
Si le modèle ne figure pas dans la liste, activez `Advanced Options`, et entrez-le dans `Custom Model` (par exemple openrouter/&lt;model-name&gt; comme `openrouter/anthropic/claude-3.5-sonnet`).
* `API Key` à votre clé API OpenRouter.
