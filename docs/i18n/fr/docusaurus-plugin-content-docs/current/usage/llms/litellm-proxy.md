

# Proxy LiteLLM

OpenHands prend en charge l'utilisation du [proxy LiteLLM](https://docs.litellm.ai/docs/proxy/quick_start) pour accéder à divers fournisseurs de LLM.

## Configuration

Pour utiliser le proxy LiteLLM avec OpenHands, vous devez :

1. Configurer un serveur proxy LiteLLM (voir la [documentation LiteLLM](https://docs.litellm.ai/docs/proxy/quick_start))
2. Lors de l'exécution d'OpenHands, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les paramètres :
  * Activer les `Options avancées`
  * `Custom Model` au préfixe `litellm_proxy/` + le modèle que vous utiliserez (par exemple, `litellm_proxy/anthropic.claude-3-5-sonnet-20241022-v2:0`)
  * `Base URL` à l'URL de votre proxy LiteLLM (par exemple, `https://your-litellm-proxy.com`)
  * `API Key` à votre clé API du proxy LiteLLM

## Modèles pris en charge

Les modèles pris en charge dépendent de la configuration de votre proxy LiteLLM. OpenHands prend en charge tous les modèles que votre proxy LiteLLM est configuré pour gérer.

Reportez-vous à la configuration de votre proxy LiteLLM pour obtenir la liste des modèles disponibles et leurs noms.
