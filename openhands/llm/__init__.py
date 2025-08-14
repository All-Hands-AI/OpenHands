# Avoid importing heavy submodules at package import time to prevent circular imports.
# Provide lazy attribute access for common exports.

__all__ = ['LLM', 'AsyncLLM', 'StreamingLLM']


def __getattr__(name):
    if name == 'LLM':
        from .llm import LLM as _LLM

        return _LLM
    if name == 'AsyncLLM':
        from .async_llm import AsyncLLM as _AsyncLLM

        return _AsyncLLM
    if name == 'StreamingLLM':
        from .streaming_llm import StreamingLLM as _StreamingLLM

        return _StreamingLLM
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
