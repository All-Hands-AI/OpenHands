if __package__ is None or __package__ == '':
    from utils import get_model_max_input_tokens
else:
    from .utils import get_model_max_input_tokens

if __package__ is None or __package__ == '':
    from repomap import RepoMap
else:
    from .repomap import RepoMap

__all__ = ['RepoMap', 'get_model_max_input_tokens']
