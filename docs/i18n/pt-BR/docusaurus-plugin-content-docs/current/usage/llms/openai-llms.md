# OpenAI

OpenHands usa o LiteLLM para fazer chamadas aos modelos de chat da OpenAI. Você pode encontrar a documentação sobre como usar a OpenAI como provedor [aqui](https://docs.litellm.ai/docs/providers/openai).

## Configuração

Ao executar o OpenHands, você precisará definir o seguinte na interface do OpenHands através das Configurações:
* `LLM Provider` para `OpenAI`
* `LLM Model` para o modelo que você usará.
[Visite aqui para ver uma lista completa dos modelos OpenAI que o LiteLLM suporta.](https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models)
Se o modelo não estiver na lista, ative as opções `Advanced` e insira-o em `Custom Model` (por exemplo, openai/&lt;nome-do-modelo&gt; como `openai/gpt-4o`).
* `API Key` para sua chave de API da OpenAI. Para encontrar ou criar sua Chave de API de Projeto OpenAI, [veja aqui](https://platform.openai.com/api-keys).

## Usando Endpoints Compatíveis com OpenAI

Assim como para as completions de chat da OpenAI, usamos o LiteLLM para endpoints compatíveis com OpenAI. Você pode encontrar a documentação completa sobre este tópico [aqui](https://docs.litellm.ai/docs/providers/openai_compatible).

## Usando um Proxy OpenAI

Se você estiver usando um proxy OpenAI, na interface do OpenHands através das Configurações:
1. Ative as opções `Advanced`
2. Defina o seguinte:
   - `Custom Model` para openai/&lt;nome-do-modelo&gt; (por exemplo, `openai/gpt-4o` ou openai/&lt;prefixo-do-proxy&gt;/&lt;nome-do-modelo&gt;)
   - `Base URL` para a URL do seu proxy OpenAI
   - `API Key` para sua chave de API da OpenAI
