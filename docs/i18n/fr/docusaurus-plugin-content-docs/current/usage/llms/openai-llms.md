# OpenAI

OpenHands utilise LiteLLM pour effectuer des appels aux modèles de chat d'OpenAI. Vous pouvez trouver leur documentation sur l'utilisation d'OpenAI comme fournisseur [ici](https://docs.litellm.ai/docs/providers/openai).

## Configuration

Lors de l'exécution d'OpenHands, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les Paramètres :
* `LLM Provider` sur `OpenAI`
* `LLM Model` sur le modèle que vous utiliserez.
[Visitez ce lien pour voir une liste complète des modèles OpenAI pris en charge par LiteLLM.](https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models)
Si le modèle ne figure pas dans la liste, activez les options `Advanced`, et saisissez-le dans `Custom Model` (par exemple openai/&lt;nom-du-modèle&gt; comme `openai/gpt-4o`).
* `API Key` avec votre clé API OpenAI. Pour trouver ou créer votre clé API de projet OpenAI, [voir ici](https://platform.openai.com/api-keys).

## Utilisation des points de terminaison compatibles avec OpenAI

Tout comme pour les compléments de chat OpenAI, nous utilisons LiteLLM pour les points de terminaison compatibles avec OpenAI. Vous pouvez trouver leur documentation complète sur ce sujet [ici](https://docs.litellm.ai/docs/providers/openai_compatible).

## Utilisation d'un proxy OpenAI

Si vous utilisez un proxy OpenAI, dans l'interface utilisateur d'OpenHands via les Paramètres :
1. Activez les options `Advanced`
2. Définissez les éléments suivants :
   - `Custom Model` sur openai/&lt;nom-du-modèle&gt; (par exemple `openai/gpt-4o` ou openai/&lt;préfixe-proxy&gt;/&lt;nom-du-modèle&gt;)
   - `Base URL` sur l'URL de votre proxy OpenAI
   - `API Key` sur votre clé API OpenAI
