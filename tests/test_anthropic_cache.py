import os

from litellm import completion, stream_chunk_builder

response = completion(
    model='litellm_proxy/claude-3-7-sonnet-20250219',
    api_key=os.getenv('LITELLM_API_KEY'),
    # base_url='https://litellm-staging.thesis.io',
    base_url='http://localhost:9545',
    messages=[
        {
            'role': 'system',
            'content': [
                {
                    'type': 'text',
                    'text': 'You are an AI assistant tasked with analyzing legal documents.',
                },
                {
                    'type': 'text',
                    'text': 'Here is the full text of a complex legal agreement' * 4000,
                    'cache_control': {'type': 'ephemeral'},
                },
            ],
        },
        {
            'role': 'user',
            'content': "What's the capital of Vietnam? Answer in two words.",
        },
    ],
    stream=True,
    stream_options={
        'include_usage': True,
    },
)

# print(response.usage)

# For streaming we iterate over the chunks
chunks = []
for chunk in response:
    chunks.append(chunk)
    if 'usage' in chunk:
        print(chunk['usage'])

data = stream_chunk_builder(chunks)

print('usage data', data.usage)

# import os
# import anthropic

# api_key = os.getenv('ANTHROPIC_API_KEY')
# client = anthropic.Anthropic(api_key=api_key)

# with client.messages.stream(
#     model="claude-3-7-sonnet-20250219",
#     max_tokens=20000,
#     system=[
#         {
#             "type": "text",
#             "text": "You are an AI assistant tasked with analyzing legal documents.",
#         },
#         {
#             "type": "text",
#             "text": "Here is the full text of a complex legal agreement" * 4000,
#             "cache_control": {"type": "ephemeral"},
#         },
#     ],
#     messages=[
#         {
#             "role": "user",
#             "content": "What's the capital of Hanoi?",
#         }
#     ],
# ) as stream:
#     for chunk in stream:
#         if isinstance(chunk, anthropic.MessageStopEvent):
#             print(chunk)
