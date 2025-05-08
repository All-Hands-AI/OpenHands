# OpenRouter

OpenHands usa o LiteLLM para fazer chamadas a modelos de chat no OpenRouter. Você pode encontrar a documentação sobre como usar o OpenRouter como provedor [aqui](https://docs.litellm.ai/docs/providers/openrouter).

## Configuração

Ao executar o OpenHands, você precisará definir o seguinte na interface do OpenHands através das Configurações:
* `LLM Provider` para `OpenRouter`
* `LLM Model` para o modelo que você usará.
[Visite aqui para ver uma lista completa de modelos do OpenRouter](https://openrouter.ai/models).
Se o modelo não estiver na lista, ative as opções `Advanced` e insira-o em `Custom Model` (por exemplo, openrouter/&lt;nome-do-modelo&gt; como `openrouter/anthropic/claude-3.5-sonnet`).
* `API Key` para sua chave de API do OpenRouter.
