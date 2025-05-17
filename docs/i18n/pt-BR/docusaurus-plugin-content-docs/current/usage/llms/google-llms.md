# Google Gemini/Vertex

O OpenHands usa o LiteLLM para fazer chamadas aos modelos de chat do Google. Você pode encontrar a documentação sobre como usar o Google como provedor:

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## Configurações do Gemini - Google AI Studio

Ao executar o OpenHands, você precisará definir o seguinte na interface do OpenHands através das Configurações:
- `LLM Provider` para `Gemini`
- `LLM Model` para o modelo que você usará.
Se o modelo não estiver na lista, ative as opções `Advanced` e insira-o em `Custom Model` (por exemplo, gemini/&lt;nome-do-modelo&gt; como `gemini/gemini-2.0-flash`).
- `API Key` para sua chave de API do Gemini

## Configurações do VertexAI - Google Cloud Platform

Para usar o Vertex AI através do Google Cloud Platform ao executar o OpenHands, você precisará definir as seguintes variáveis de ambiente usando `-e` no [comando docker run](../installation#running-openhands):

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-da-conta-de-serviço-gcp-json>"
VERTEXAI_PROJECT="<seu-id-de-projeto-gcp>"
VERTEXAI_LOCATION="<sua-localização-gcp>"
```

Em seguida, defina o seguinte na interface do OpenHands através das Configurações:
- `LLM Provider` para `VertexAI`
- `LLM Model` para o modelo que você usará.
Se o modelo não estiver na lista, ative as opções `Advanced` e insira-o em `Custom Model` (por exemplo, vertex_ai/&lt;nome-do-modelo&gt;).
