import os

from dotenv import dotenv_values


def maybe_init_laminar():
    """Initialize Laminar if the environment variables are set.

    Example configuration:
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://otel-collector:4317/v1/traces

    # comma separated, key=value url-encoded pairs
    OTEL_EXPORTER_OTLP_TRACES_HEADERS="Authorization=Bearer%20<KEY>,X-Key=<CUSTOM_VALUE>"

    # grpc is assumed if not specified
    OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf # or grpc/protobuf
    # or
    OTEL_EXPORTER=otlp_http # or otlp_grpc
    """
    dotenv_vals = dotenv_values()
    keys = [
        'LMNR_PROJECT_API_KEY',
        'OTEL_ENDPOINT',
        'OTEL_EXPORTER_OTLP_TRACES_ENDPOINT',
        'OTEL_EXPORTER_OTLP_ENDPOINT',
    ]
    if any(dotenv_vals.get(key) for key in keys) or any(os.getenv(key) for key in keys):
        import litellm
        from lmnr import Laminar, LaminarLiteLLMCallback

        Laminar.initialize()
        litellm.callbacks.append(LaminarLiteLLMCallback())
