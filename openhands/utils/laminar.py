import os


def maybe_init_laminar():
    if os.getenv('LMNR_PROJECT_API_KEY'):
        import litellm
        from lmnr import Laminar, LaminarLiteLLMCallback

        Laminar.initialize()
        litellm.callbacks.append(LaminarLiteLLMCallback())
