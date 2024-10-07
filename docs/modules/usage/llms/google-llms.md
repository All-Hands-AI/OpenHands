# Google Gemini/Vertex

OpenHands uses LiteLLM to make calls to Google's chat models. You can find their documentation on using Google as a provider:

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## Gemini - Google AI Studio Configs

When running OpenHands, you'll need to set the following in the OpenHands UI through the Settings:
* `LLM Provider` to `Gemini`
* `LLM Model` to the model you will be using.
If the model is not in the list, toggle `Advanced Options`, and enter it in `Custom Model` (e.g. gemini/&lt;model-name&gt; like `gemini/gemini-1.5-pro`).
* `API Key` to your Gemini API key

## VertexAI - Google Cloud Platform Configs

To use Vertex AI through Google Cloud Platform when running OpenHands, you'll need to set the following environment
variables using `-e` in the [docker run command](/modules/usage/installation):

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
```

Then set the following in the OpenHands UI through the Settings:
* `LLM Provider` to `VertexAI`
* `LLM Model` to the model you will be using.
If the model is not in the list, toggle `Advanced Options`, and enter it in `Custom Model` (e.g. vertex_ai/&lt;model-name&gt;).
