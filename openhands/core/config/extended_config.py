class ExtendedConfig:
    """Configuration for extended functionalities.

    Attributes:
        Values depend on the defined section
    """

    extended: dict = {}

    def __str__(self):
        attr_str = []
        for key_name, dict_value in self.extended.items():
            for attr_name, attr_value in dict_value.items():
                attr_str.append(f'[{key_name}]{attr_name}={repr(attr_value)}')
        return f"ExtendedConfig({', '.join(attr_str)})"

    def add_dict(self, key: str, extended_config_dict: dict) -> 'ExtendedConfig':
        self.extended[key] = extended_config_dict
        return self

    def get(self, key: str) -> dict:
        return self.extended[key]

    def __getitem__(self, key):
        return self.get(key)

    def __repr__(self):
        return self.__str__()
