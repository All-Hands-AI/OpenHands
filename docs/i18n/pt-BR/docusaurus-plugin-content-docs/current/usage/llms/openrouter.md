Here is the translated content in Brazilian Portuguese:

# OpenRouter

O OpenHands usa o LiteLLM para fazer chamadas para modelos de chat no OpenRouter. Você pode encontrar a documentação deles sobre como usar o OpenRouter como provedor [aqui](https://docs.litellm.ai/docs/providers/openrouter).

## Configuração

Ao executar o OpenHands, você precisará definir o seguinte na interface do usuário do OpenHands através das Configurações:
* `LLM Provider` para `OpenRouter`
* `LLM Model` para o modelo que você usará.
[Visite aqui para ver uma lista completa de modelos do OpenRouter](https://openrouter.ai/models).
Se o modelo não estiver na lista, ative as opções `Advanced` e insira-o em `Custom Model` (por exemplo, openrouter/&lt;model-name&gt; como `openrouter/anthropic/claude-3.5-sonnet`).
* `API Key` para a sua chave de API do OpenRouter.
