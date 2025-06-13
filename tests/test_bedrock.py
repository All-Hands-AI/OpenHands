import os
from datetime import datetime

import boto3

access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION_NAME')

# Initialize Bedrock client
bedrock = boto3.client(
    'bedrock-runtime',
    region_name=region_name,
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    endpoint_url='https://bedrock-runtime.us-east-2.amazonaws.com',
)

# Define a simple tool
tools = [
    {
        'toolSpec': {
            'name': 'get_current_time',
            'description': 'Get the current time' * 5000,
            'inputSchema': {
                'json': {'type': 'object', 'properties': {}, 'required': []}
            },
        },
    },
    {'cachePoint': {'type': 'default'}},
]

# System prompt
system_prompt = [
    {
        'text': 'You are a helpful assistant that provides accurate information and can use tools to answer questions.'
        * 5000,
    },
    {'cachePoint': {'type': 'default'}},
]

# Initialize conversation history
conversation_history = []

# Store cache metadata for comparison
cache_metadata = []


def converse_with_bedrock(messages, turn):
    try:
        response = bedrock.converse(
            modelId='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
            messages=messages,
            system=system_prompt,
            toolConfig={'tools': tools},  # Move tools to toolConfig
            inferenceConfig={
                'maxTokens': 20000,
                'temperature': 0.7,
            },
        )

        print(response)

        # Extract cache metadata from response
        cache_info = {
            'turn': turn,
            'cache_read': response.get('ResponseMetadata', {})
            .get('HTTPHeaders', {})
            .get('x-amzn-bedrock-prompt-cache-read', '0'),
            'cache_write': response.get('ResponseMetadata', {})
            .get('HTTPHeaders', {})
            .get('x-amzn-bedrock-prompt-cache-write', '0'),
            'cache_read_tokens': response.get('usage', {}).get(
                'cacheReadInputTokens', 0
            ),
            'cache_write_tokens': response.get('usage', {}).get(
                'cacheWriteInputTokens', 0
            ),
            'total_tokens': response.get('usage', {}).get('totalTokens', 0),
        }
        cache_metadata.append(cache_info)

        # Process response
        output = response['output']['message']['content']
        assistant_response = {'role': 'assistant', 'content': output}

        # Handle tool use
        tool_use_id = None
        for content in output:
            if (
                'toolUse' in content
                and content['toolUse']['name'] == 'get_current_time'
            ):
                tool_use_id = content['toolUse']['toolUseId']
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f'Turn {turn} - Current time: {current_time}')
            elif 'text' in content:
                print(f"Turn {turn} - Assistant response: {content['text']}")

        return assistant_response, tool_use_id

    except Exception as e:
        print(f'Error in turn {turn}: {str(e)}')
        return None, None


last_tool_use_id = None
# Simulate 3 turns
for turn in range(1, 4):
    # Add tool_result for the previous turn's tool_use, if any
    if turn > 1 and 'last_tool_use_id' in locals() and last_tool_use_id:
        tool_result_message = {
            'role': 'user',
            'content': [
                {
                    'toolResult': {
                        'toolUseId': last_tool_use_id,
                        'content': [
                            {'json': {'time': datetime.now().strftime('%H:%M:%S')}}
                        ],
                    }
                },
                {'cachePoint': {'type': 'default'}},
            ],
        }
        conversation_history.append(tool_result_message)

    # Add new user message for the current turn
    user_message = {
        'role': 'user',
        'content': [
            {'text': f"What's the current time? (Turn {turn})"},
        ],
    }
    conversation_history.append(user_message)

    print(f'\n--- Processing Turn {turn} ---')
    # Call Converse API with the updated conversation history
    assistant_response, tool_use_id = converse_with_bedrock(conversation_history, turn)

    if assistant_response:
        # Append assistant response to conversation history
        conversation_history.append(assistant_response)
        # Store tool_use_id for the next turn
        last_tool_use_id = tool_use_id

# Compare cache read and write
print('\n--- Cache Comparison ---')
if cache_metadata:
    for i in range(len(cache_metadata)):
        print(
            f"Turn {cache_metadata[i]['turn']}: "
            f"Cache Read = {cache_metadata[i]['cache_read']}, "
            f"Cache Write = {cache_metadata[i]['cache_write']}, "
            f"Cache Read Tokens = {cache_metadata[i]['cache_read_tokens']}, "
            f"Cache Write Tokens = {cache_metadata[i]['cache_write_tokens']}, "
            f"Total Tokens = {cache_metadata[i]['total_tokens']}"
        )

    # Verify incremental caching logic
    for turn in range(2, 4):
        if turn <= len(cache_metadata):
            prev_turn = turn - 1
            cache_read_current = int(cache_metadata[turn - 1]['cache_read'] or 0)
            cache_read_prev = int(cache_metadata[prev_turn - 1]['cache_read'] or 0)
            cache_write_prev = int(cache_metadata[prev_turn - 1]['cache_write'] or 0)

            # Token-based verification
            cache_read_tokens_current = cache_metadata[turn - 1]['cache_read_tokens']
            cache_read_tokens_prev = cache_metadata[prev_turn - 1]['cache_read_tokens']
            cache_write_tokens_prev = cache_metadata[prev_turn - 1][
                'cache_write_tokens'
            ]

            print(f'\nVerifying Turn {turn}:')
            print(f'Cache Read Turn {turn} = {cache_read_current}')
            print(
                f'Cache Read Turn {prev_turn} + Cache Write Turn {prev_turn} = {cache_read_prev} + {cache_write_prev} = {cache_read_prev + cache_write_prev}'
            )
            print(f'Cache Read Tokens Turn {turn} = {cache_read_tokens_current}')
            print(
                f'Cache Read Tokens Turn {prev_turn} + Cache Write Tokens Turn {prev_turn} = {cache_read_tokens_prev} + {cache_write_tokens_prev} = {cache_read_tokens_prev + cache_write_tokens_prev}'
            )

            if cache_read_current == cache_read_prev + cache_write_prev:
                print(f'Verification passed for Turn {turn} (cache read/write)')
            else:
                print(f'Verification failed for Turn {turn} (cache read/write)')

            if (
                cache_read_tokens_current
                == cache_read_tokens_prev + cache_write_tokens_prev
            ):
                print(f'Verification passed for Turn {turn} (token counts)')
            else:
                print(f'Verification failed for Turn {turn} (token counts)')
        else:
            print(
                f'\nSkipping verification for Turn {turn}: Insufficient cache metadata'
            )
else:
    print(
        'No cache metadata available for comparison. Prompt caching may not be supported for this model.'
    )
