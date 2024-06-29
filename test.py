from litellm import completion

messages = [{'role': 'user', 'content': 'what llm are you'}]
response = completion(
    model='openai/meta-llama/Meta-Llama-3-70B-Instruct',  # add a vllm prefix so litellm knows the custom_llm_provider==vllm
    # model = "gradientai/Llama-3-70B-Instruct-Gradient-262k",
    messages=messages,
    api_key='sk-1234',
    api_base='http://localhost:8000/v1/',
    # api_base="http://localhost:8002/v1/",
    temperature=0.2,
    max_tokens=80,
)
