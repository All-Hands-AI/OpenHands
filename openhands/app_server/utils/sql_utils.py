from pydantic import SecretStr, TypeAdapter
from sqlalchemy import JSON, String, TypeDecorator


def create_json_type_decorator(object_type: type):
    """Create a decorator for a particular type. Introduced because SQLAlchemy could not process lists of enum values."""
    type_adapter: TypeAdapter = TypeAdapter(object_type)

    class JsonTypeDecorator(TypeDecorator):
        impl = JSON
        cache_ok = True

        def process_bind_param(self, value, dialect):
            return type_adapter.dump_python(
                value, mode='json', context={'expose_secrets': True}
            )

        def process_result_param(self, value, dialect):
            return type_adapter.validate_python(value)

    return JsonTypeDecorator


class SecretStrDecorator(TypeDecorator):
    """TypeDecorator for secret strings. Encrypts the value using the default key before storing."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            from openhands.app_server.config import (
                get_global_config, resolve_jwt_service
            )

            service = resolve_jwt_service(get_global_config())
            token = service.create_jwe_token({'v': value.get_secret_value()})
            return token
        return None

    def process_result_param(self, value, dialect):
        if value is not None:
            from openhands.app_server.config import (
                get_global_config, resolve_jwt_service
            )

            service = resolve_jwt_service(get_global_config())
            token = service.decrypt_jwe_token(value)
            return SecretStr(token['v'])
        return None
