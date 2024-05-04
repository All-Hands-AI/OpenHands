
class Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        else:
            # allow updates, just update existing instance
            # perhaps not the most orthodox way to do it, though it simplifies client code
            # useful for pre-defined groups of settings
            instance = cls._instances[cls]
            for key, value in kwargs.items():
                setattr(instance, key, value)
        return cls._instances[cls]
