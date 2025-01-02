class ExtendedConfig:
    """Configuration for extended functionalities.

    Attributes:
        Values depend on the defined section
    """

    extended: dict = {}

    def __str__(self):
        attr_str = []
        for attr_name, attr_value in self.extended.items():
            attr_str.append(f'{attr_name}={repr(attr_value)}')
        return f"ExtendedConfig({', '.join(attr_str)})"

    @classmethod
    def from_dict(cls, extended_config_dict: dict) -> 'ExtendedConfig':
        return cls(extended_config_dict)

    def __init__(self, dict=None):
        self.extended = dict

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, key):
        return self.extended[key]

    def __getattr__(self, key):
        return self.extended[key]
