# Groq

OpenHands usa LiteLLM para fazer chamadas a modelos de chat no Groq. Você pode encontrar a documentação sobre como usar o Groq como provedor [aqui](https://docs.litellm.ai/docs/providers/groq).

## Configuração

Ao executar o OpenHands, você precisará definir o seguinte na interface do OpenHands através das Configurações:
- `LLM Provider` para `Groq`
- `LLM Model` para o modelo que você usará. [Visite aqui para ver a lista de
modelos que o Groq hospeda](https://console.groq.com/docs/models). Se o modelo não estiver na lista, ative
as opções `Advanced` e insira-o em `Custom Model` (por exemplo, groq/&lt;nome-do-modelo&gt; como `groq/llama3-70b-8192`).
- `API key` para sua chave de API do Groq. Para encontrar ou criar sua chave de API do Groq, [veja aqui](https://console.groq.com/keys).



## Usando o Groq como um Endpoint Compatível com OpenAI

O endpoint do Groq para chat completion é [majoritariamente compatível com OpenAI](https://console.groq.com/docs/openai). Portanto, você pode acessar os modelos do Groq como
acessaria qualquer endpoint compatível com OpenAI. Na interface do OpenHands através das Configurações:
1. Ative as opções `Advanced`
2. Configure o seguinte:
   - `Custom Model` com o prefixo `openai/` + o modelo que você usará (por exemplo, `openai/llama3-70b-8192`)
   - `Base URL` para `https://api.groq.com/openai/v1`
   - `API Key` para sua chave de API do Groq
