from openhands.core.message import Message


def apply_prompt_caching(messages: list[Message]) -> None:
    """Applies caching breakpoints to the messages."""
    # NOTE: this is only needed for anthropic
    # following logic here:
    # https://github.com/anthropics/anthropic-quickstarts/blob/8f734fd08c425c6ec91ddd613af04ff87d70c5a0/computer-use-demo/computer_use_demo/loop.py#L241-L262
    breakpoints_remaining = 3  # remaining 1 for system/tool
    for message in reversed(messages):
        if message.role in ('user', 'tool'):
            if breakpoints_remaining > 0:
                message.content[
                    -1
                ].cache_prompt = True  # Last item inside the message content
                breakpoints_remaining -= 1
            else:
                break
