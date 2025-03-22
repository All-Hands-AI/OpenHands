# Google Gemini/Vertex

O OpenHands usa o LiteLLM para fazer chamadas aos modelos de chat do Google. Você pode encontrar a documentação sobre como usar o Google como provedor:

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## Configurações do Gemini - Google AI Studio

Ao executar o OpenHands, você precisará definir o seguinte na interface do usuário do OpenHands através das Configurações:
- `LLM Provider` para `Gemini`
- `LLM Model` para o modelo que você usará.
Se o modelo não estiver na lista, ative as opções `Advanced` e insira-o em `Custom Model` (por exemplo, gemini/&lt;model-name&gt; como `gemini/gemini-1.5-pro`).
- `API Key` para sua chave de API do Gemini

## Configurações do VertexAI - Google Cloud Platform

Para usar o Vertex AI através do Google Cloud Platform ao executar o OpenHands, você precisará definir as seguintes variáveis de ambiente usando `-e` no [comando docker run](../installation#running-openhands):

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
```

Em seguida, defina o seguinte na interface do usuário do OpenHands através das Configurações:
- `LLM Provider` para `VertexAI`
- `LLM Model` para o modelo que você usará.
Se o modelo não estiver na lista, ative as opções `Advanced` e insira-o em `Custom Model` (por exemplo, vertex_ai/&lt;model-name&gt;).
