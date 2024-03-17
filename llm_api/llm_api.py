import os
from llm_api.litellm import litellm
from typing import Union
from typing import List, Optional, Union
from litellm.utils import CustomStreamWrapper,ModelResponse
import os
from llm_api.llm_statistics import llm_statistics


######################
# MODEL AND SUBMODEL #
######################

if os.environ.get('platform') in ["openai", "azure", "sagemaker", "bedrock", "vertex_ai", "palm", "gemini", "mistral", "cloudflare", "cohere", "anthropic", "huggingface", 
                                  "replicate", "together_ai", "openrouter", "ai21", "baseten", "vllm", "nlp_cloud", "aleph_alpha", "petals", "ollama", "deepinfra", 
                                  "perplexity", "groq", "anyscale", "voyage", "xinference"]:
    api = litellm()


def request_model(
        # Optional OpenAI params: see https://platform.openai.com/docs/api-reference/chat/create
        messages: List = [],
        timeout: Optional[Union[float, int]] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stream: Optional[bool] = None,
        stop=None,
        max_tokens: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[dict] = None,
        user: Optional[str] = None,
        # openai v1.0+ new params
        response_format: Optional[dict] = None,
        seed: Optional[int] = None,
        tools: Optional[List] = None,
        tool_choice: Optional[str] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        deployment_id=None,
        extra_headers: Optional[dict] = None,
        # soon to be deprecated params by OpenAI
        functions: Optional[List] = None,
        function_call: Optional[str] = None,
    ) -> Union[ModelResponse, CustomStreamWrapper]:

        response = api.request_model(
                            messages=messages,
                            timeout = timeout,
                            temperature = temperature,
                            top_p = top_p,
                            n = n,
                            stream = stream,
                            stop=stop,
                            max_tokens = max_tokens,
                            presence_penalty = presence_penalty,
                            frequency_penalty = frequency_penalty,
                            logit_bias = logit_bias,
                            user = user,
                            response_format = response_format,
                            seed = seed,
                            tools = tools,
                            tool_choice = tool_choice,
                            logprobs = logprobs,
                            top_logprobs = top_logprobs,
                            deployment_id=deployment_id,
                            extra_headers = extra_headers,
                            functions = functions,
                            function_call = function_call,
                        )

        llm_statistics.use_token(response[0])

        return response


def request_submodel(
        # Optional OpenAI params: see https://platform.openai.com/docs/api-reference/chat/create
        messages: List = [],
        timeout: Optional[Union[float, int]] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stream: Optional[bool] = None,
        stop=None,
        max_tokens: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[dict] = None,
        user: Optional[str] = None,
        # openai v1.0+ new params
        response_format: Optional[dict] = None,
        seed: Optional[int] = None,
        tools: Optional[List] = None,
        tool_choice: Optional[str] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        deployment_id=None,
        extra_headers: Optional[dict] = None,
        # soon to be deprecated params by OpenAI
        functions: Optional[List] = None,
        function_call: Optional[str] = None,
    ) -> Union[ModelResponse, CustomStreamWrapper]:

        response = api.request_submodel(
                            messages=messages,
                            timeout = timeout,
                            temperature = temperature,
                            top_p = top_p,
                            n = n,
                            stream = stream,
                            stop=stop,
                            max_tokens = max_tokens,
                            presence_penalty = presence_penalty,
                            frequency_penalty = frequency_penalty,
                            logit_bias = logit_bias,
                            user = user,
                            response_format = response_format,
                            seed = seed,
                            tools = tools,
                            tool_choice = tool_choice,
                            logprobs = logprobs,
                            top_logprobs = top_logprobs,
                            deployment_id=deployment_id,
                            extra_headers = extra_headers,
                            functions = functions,
                            function_call = function_call,
                        )

        llm_statistics.use_subtoken(response[0])

        return response



###################
# EMBEDDING MODEL #
###################

if os.environ.get('embed_platform') in ["openai", "azure", "sagemaker", "bedrock", "vertex_ai", "palm", "gemini", "mistral", "cloudflare", "cohere", "anthropic", "huggingface", 
                                        "replicate", "together_ai", "openrouter", "ai21", "baseten", "vllm", "nlp_cloud", "aleph_alpha", "petals", "ollama", "deepinfra", 
                                        "perplexity", "groq", "anyscale", "voyage", "xinference"]:
    embed_api = litellm()

def request_embed_model(
        input=[],
        # Optional params
        dimensions: Optional[int] = None,
        timeout=600,  # default to 10 minutes
        caching: bool = False,
        user: Optional[str] = None,
        litellm_call_id=None,
        litellm_logging_obj=None,
        logger_fn=None,
    ):
    
        response = embed_api.request_embed_model(
                            input=input,
                            dimensions = dimensions,
                            timeout=timeout, 
                            caching = caching,
                            user = user,
                            litellm_call_id=litellm_call_id,
                            litellm_logging_obj=litellm_logging_obj,
                            logger_fn=logger_fn,
                        )

        llm_statistics.use_embed_token(response)

        return response