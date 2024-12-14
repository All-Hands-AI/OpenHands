

# Groq

OpenHands utilise LiteLLM pour faire des appels aux modèles de chat sur Groq. Vous pouvez trouver leur documentation sur l'utilisation de Groq comme fournisseur [ici](https://docs.litellm.ai/docs/providers/groq).

## Configuration

Lorsque vous exécutez OpenHands, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les paramètres :
* `LLM Provider` à `Groq`
* `LLM Model` au modèle que vous utiliserez. [Visitez ici pour voir la liste des modèles hébergés par Groq](https://console.groq.com/docs/models). Si le modèle n'est pas dans la liste, activez les `Advanced Options` et entrez-le dans `Custom Model` (par exemple, groq/&lt;model-name&gt; comme `groq/llama3-70b-8192`).
* `API key` à votre clé API Groq. Pour trouver ou créer votre clé API Groq, [voir ici](https://console.groq.com/keys).



## Utilisation de Groq comme point de terminaison compatible OpenAI

Le point de terminaison Groq pour la complétion de chat est [principalement compatible OpenAI](https://console.groq.com/docs/openai). Par conséquent, vous pouvez accéder aux modèles Groq comme vous le feriez pour n'importe quel point de terminaison compatible OpenAI. Vous pouvez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les paramètres :
* Activer les `Advanced Options`
* `Custom Model` au préfixe `openai/` + le modèle que vous utiliserez (par exemple, `openai/llama3-70b-8192`)
* `Base URL` à `https://api.groq.com/openai/v1`
* `API Key` à votre clé API Groq
