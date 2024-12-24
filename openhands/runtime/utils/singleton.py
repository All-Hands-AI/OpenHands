class Singleton(type):
    """Metaclass for creating singleton classes.

    Usage:
        class MyClass(metaclass=Singleton):
            pass
    """

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
