# Running LLMs on Groq

OpenHands uses LiteLLM to make calls to chat models on Groq. You can find their full documentation on using Groq as provider [here](https://docs.litellm.ai/docs/providers/groq).

## Configuration

When running OpenHands, you'll need to set the following in the OpenHands UI through the Settings:
* `LLM Provider` to `Groq`
* `LLM Model` to the model you will be using
* `API key` to your Groq API key. To find or create your Groq API Key, [see **here**](https://console.groq.com/keys).

Visit [here](https://console.groq.com/docs/models) to see the list of models that Groq hosts.

## Using Groq as an OpenAI-Compatible Endpoint

The Groq endpoint for chat completion is [mostly OpenAI-compatible](https://console.groq.com/docs/openai). Therefore, if you wish, you can access Groq models as you would access any OpenAI-compatible endpoint. You can toggle `Advanced Options` and set the following:
* `Custom Model` to the prefix `openai/` + the model you will be using, e.g. `openai/llama3-8b-8192`
* `API Key` to your Groq API key
* `Base URL` to `https://api.groq.com/openai/v1`
