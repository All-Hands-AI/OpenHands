# Groq

OpenHands uses LiteLLM to make calls to chat models on Groq. You can find their full documentation on using Groq as provider [here](https://docs.litellm.ai/docs/providers/groq).

## Configuration

When running OpenHands, you'll need to set the following in the OpenHands UI through the Settings:
* `LLM Provider` to `Groq`
* `LLM Model` to the model you will be using. [Visit **here** to see the list of
models that Groq hosts](https://console.groq.com/docs/models). If the model is not in the list, toggle
`Advanced Options`, and enter it in `Custom Model` (i.e. groq/&lt;model-name&gt;)
* `API key` to your Groq API key. To find or create your Groq API Key, [see **here**](https://console.groq.com/keys)



## Using Groq as an OpenAI-Compatible Endpoint

The Groq endpoint for chat completion is [mostly OpenAI-compatible](https://console.groq.com/docs/openai). Therefore, you can access Groq models as you
would access any OpenAI-compatible endpoint. You can set the following in the OpenHands UI through the Settings:
* Enable `Advanced Options`
* `Custom Model` to the prefix `openai/` + the model you will be using (Example: `openai/llama3-8b-8192`)
* `Base URL` to `https://api.groq.com/openai/v1`
* `API Key` to your Groq API key
