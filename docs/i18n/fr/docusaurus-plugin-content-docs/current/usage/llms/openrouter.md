# OpenRouter

OpenHands utilise LiteLLM pour effectuer des appels aux modèles de chat sur OpenRouter. Vous pouvez trouver leur documentation sur l'utilisation d'OpenRouter comme fournisseur [ici](https://docs.litellm.ai/docs/providers/openrouter).

## Configuration

Lors de l'exécution d'OpenHands, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les Paramètres :
* `LLM Provider` sur `OpenRouter`
* `LLM Model` sur le modèle que vous utiliserez.
[Visitez ce lien pour voir une liste complète des modèles OpenRouter](https://openrouter.ai/models).
Si le modèle ne figure pas dans la liste, activez les options `Advanced`, et saisissez-le dans `Custom Model` (par exemple openrouter/&lt;nom-du-modèle&gt; comme `openrouter/anthropic/claude-3.5-sonnet`).
* `API Key` avec votre clé API OpenRouter.
