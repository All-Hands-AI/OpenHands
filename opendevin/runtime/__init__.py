from .e2b.runtime import E2BRuntime
from .runtime import Runtime

__all__ = ['Runtime', 'E2BRuntime', 'get_runtime']


def get_runtime(name):
    if name == 'local':
        # return LocalRuntime()
        raise NotImplementedError('Local runtime not implemented')
    elif name == 'ssh':
        # return DockerSSHRuntime()
        raise NotImplementedError('SSH runtime not implemented')
    elif name == 'e2b':
        return E2BRuntime()
    else:
        raise ValueError(f'Runtime {name} not supported')
