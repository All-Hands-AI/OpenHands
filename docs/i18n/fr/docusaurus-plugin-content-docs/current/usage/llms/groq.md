# Groq

OpenHands utilise LiteLLM pour effectuer des appels aux modèles de chat sur Groq. Vous pouvez trouver leur documentation sur l'utilisation de Groq comme fournisseur [ici](https://docs.litellm.ai/docs/providers/groq).

## Configuration

Lors de l'exécution d'OpenHands, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les Paramètres :
- `LLM Provider` sur `Groq`
- `LLM Model` sur le modèle que vous utiliserez. [Visitez ce lien pour voir la liste des
modèles hébergés par Groq](https://console.groq.com/docs/models). Si le modèle n'est pas dans la liste, activez
les options `Advanced`, et saisissez-le dans `Custom Model` (par exemple groq/&lt;nom-du-modèle&gt; comme `groq/llama3-70b-8192`).
- `API key` avec votre clé API Groq. Pour trouver ou créer votre clé API Groq, [voir ici](https://console.groq.com/keys).

## Utilisation de Groq comme point de terminaison compatible OpenAI

Le point de terminaison Groq pour la complétion de chat est [majoritairement compatible avec OpenAI](https://console.groq.com/docs/openai). Par conséquent, vous pouvez accéder aux modèles Groq comme vous
accéderiez à n'importe quel point de terminaison compatible OpenAI. Dans l'interface utilisateur d'OpenHands via les Paramètres :
1. Activez les options `Advanced`
2. Définissez les éléments suivants :
   - `Custom Model` avec le préfixe `openai/` + le modèle que vous utiliserez (par exemple `openai/llama3-70b-8192`)
   - `Base URL` sur `https://api.groq.com/openai/v1`
   - `API Key` avec votre clé API Groq
