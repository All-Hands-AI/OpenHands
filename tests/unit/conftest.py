def pytest_configure(config):
    config.option.verbose = 1  # Enable verbose output (-v)
    config.option.capture = 'no'  # Disable output capturing (-s)
