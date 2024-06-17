import litellm

litellm.set_verbose = True

response = litellm.completion(
    model='openai/Qwen2-72B-Instruct',
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Who won the world series in 2020?'},
    ],
    base_url='http://cccxc708.pok.ibm.com:8000/v1',
    api_key='fake',
)
print(response)
