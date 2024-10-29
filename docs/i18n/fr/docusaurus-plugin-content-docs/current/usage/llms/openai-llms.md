

# OpenAI

OpenHands utilise LiteLLM pour effectuer des appels aux modèles de chat d'OpenAI. Vous pouvez trouver leur documentation sur l'utilisation d'OpenAI en tant que fournisseur [ici](https://docs.litellm.ai/docs/providers/openai).

## Configuration

Lors de l'exécution d'OpenHands, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les paramètres :
* `LLM Provider` à `OpenAI`
* `LLM Model` au modèle que vous utiliserez.
[Visitez ce lien pour voir une liste complète des modèles OpenAI pris en charge par LiteLLM.](https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models)
Si le modèle ne figure pas dans la liste, activez les `Advanced Options` et entrez-le dans `Custom Model` (par exemple, openai/&lt;model-name&gt; comme `openai/gpt-4o`).
* `API Key` à votre clé API OpenAI. Pour trouver ou créer votre clé API de projet OpenAI, [voir ici](https://platform.openai.com/api-keys).

## Utilisation des endpoints compatibles OpenAI

Tout comme pour les chat completions OpenAI, nous utilisons LiteLLM pour les endpoints compatibles OpenAI. Vous pouvez trouver leur documentation complète sur ce sujet [ici](https://docs.litellm.ai/docs/providers/openai_compatible).

## Utilisation d'un proxy OpenAI

Si vous utilisez un proxy OpenAI, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les paramètres :
* Activer les `Advanced Options`
* `Custom Model` à openai/&lt;model-name&gt; (par exemple, `openai/gpt-4o` ou openai/&lt;proxy-prefix&gt;/&lt;model-name&gt;)
* `Base URL` à l'URL de votre proxy OpenAI
* `API Key` à votre clé API OpenAI
