import os
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

from openhands.server.middleware import LocalhostCORSMiddleware


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    app = FastAPI()

    @app.get('/test')
    def test_endpoint():
        return {'message': 'Test endpoint'}

    return app


def test_localhost_cors_middleware_init_with_env_var():
    """Test that the middleware correctly parses PERMITTED_CORS_ORIGINS environment variable."""
    with patch.dict(
        os.environ, {'PERMITTED_CORS_ORIGINS': 'https://example.com,https://test.com'}
    ):
        app = FastAPI()
        middleware = LocalhostCORSMiddleware(app)

        # Check that the origins were correctly parsed from the environment variable
        assert 'https://example.com' in middleware.allow_origins
        assert 'https://test.com' in middleware.allow_origins
        assert len(middleware.allow_origins) == 2


def test_localhost_cors_middleware_init_without_env_var():
    """Test that the middleware works correctly without PERMITTED_CORS_ORIGINS environment variable."""
    with patch.dict(os.environ, {}, clear=True):
        app = FastAPI()
        middleware = LocalhostCORSMiddleware(app)

        # Check that allow_origins is empty when no environment variable is set
        assert middleware.allow_origins == ()


def test_localhost_cors_middleware_is_allowed_origin_localhost(app):
    """Test that localhost origins are allowed regardless of port when no explicit CORS settings are provided."""
    # The middleware only allows localhost origins if both allow_origins and allow_origin_regex are empty
    with patch.dict(
        os.environ, {}, clear=True
    ):  # Ensure no environment variables are set
        middleware = LocalhostCORSMiddleware(app)

        # Test with localhost
        assert middleware.is_allowed_origin('http://localhost:8000') is True

        # Test with different port
        assert middleware.is_allowed_origin('http://localhost:3000') is True

        # Test with 127.0.0.1
        assert middleware.is_allowed_origin('http://127.0.0.1:8000') is True


def test_localhost_cors_middleware_is_allowed_origin_non_localhost(app):
    """Test that non-localhost origins follow the standard CORS rules."""
    # Set up the middleware with specific allowed origins
    with patch.dict(os.environ, {'PERMITTED_CORS_ORIGINS': 'https://example.com'}):
        app.add_middleware(LocalhostCORSMiddleware)
        client = TestClient(app)

        # Test with allowed origin
        response = client.get('/test', headers={'Origin': 'https://example.com'})
        assert response.status_code == 200
        assert response.headers['access-control-allow-origin'] == 'https://example.com'

        # Test with disallowed origin
        response = client.get('/test', headers={'Origin': 'https://disallowed.com'})
        assert response.status_code == 200
        # The disallowed origin should not be in the response headers
        assert 'access-control-allow-origin' not in response.headers


def test_localhost_cors_middleware_missing_origin(app):
    """Test behavior when Origin header is missing."""
    app.add_middleware(LocalhostCORSMiddleware)
    client = TestClient(app)

    # Test without Origin header
    response = client.get('/test')
    assert response.status_code == 200
    # There should be no access-control-allow-origin header
    assert 'access-control-allow-origin' not in response.headers


def test_localhost_cors_middleware_inheritance():
    """Test that LocalhostCORSMiddleware correctly inherits from CORSMiddleware."""
    assert issubclass(LocalhostCORSMiddleware, CORSMiddleware)


def test_localhost_cors_middleware_cors_parameters():
    """Test that CORS parameters are set correctly in the middleware."""
    # We need to inspect the initialization parameters rather than attributes
    # since CORSMiddleware doesn't expose these as attributes
    with patch('fastapi.middleware.cors.CORSMiddleware.__init__') as mock_init:
        mock_init.return_value = None
        app = FastAPI()
        LocalhostCORSMiddleware(app)

        # Check that the parent class was initialized with the correct parameters
        mock_init.assert_called_once()
        _, kwargs = mock_init.call_args

        assert kwargs['allow_credentials'] is True
        assert kwargs['allow_methods'] == ['*']
        assert kwargs['allow_headers'] == ['*']


def test_localhost_cors_middleware_with_regex():
    """Test that the middleware correctly uses the regex pattern from the environment variable."""
    regex_pattern = r'.*\.staging\.all-hands\.dev'

    with patch.dict(os.environ, {'PERMITTED_CORS_REGEX': regex_pattern}):
        app = FastAPI()
        LocalhostCORSMiddleware(app)

        # Check that the regex pattern was correctly passed to the parent class
        with patch('fastapi.middleware.cors.CORSMiddleware.__init__') as mock_init:
            mock_init.return_value = None
            app = FastAPI()
            LocalhostCORSMiddleware(app)

            # Check that the parent class was initialized with the correct regex
            _, kwargs = mock_init.call_args
            assert kwargs['allow_origin_regex'] == regex_pattern


def test_localhost_cors_middleware_is_allowed_origin_with_regex(app):
    """Test that origins matching the regex pattern are allowed."""
    regex_pattern = r'.*\.staging\.all-hands\.dev'

    with patch.dict(os.environ, {'PERMITTED_CORS_REGEX': regex_pattern}):
        middleware = LocalhostCORSMiddleware(app)

        # Test with an origin that matches the regex pattern
        assert (
            middleware.is_allowed_origin('https://example.staging.all-hands.dev')
            is True
        )

        # Test with another origin that matches the regex pattern
        assert middleware.is_allowed_origin('http://test.staging.all-hands.dev') is True

        # Test with an origin that doesn't match the regex pattern
        assert (
            middleware.is_allowed_origin('https://example.prod.all-hands.dev') is False
        )
        assert middleware.is_allowed_origin('https://all-hands.dev') is False


def test_localhost_cors_middleware_regex_prioritized_over_localhost(app):
    """Test that when a regex pattern is set, localhost origins are not automatically allowed."""
    regex_pattern = r'.*\.staging\.all-hands\.dev'

    with patch.dict(os.environ, {'PERMITTED_CORS_REGEX': regex_pattern}):
        middleware = LocalhostCORSMiddleware(app)

        # Localhost origins should not be automatically allowed when a regex pattern is set
        assert middleware.is_allowed_origin('http://localhost:8000') is False
        assert middleware.is_allowed_origin('http://127.0.0.1:3000') is False

        # But origins matching the regex pattern are still allowed
        assert (
            middleware.is_allowed_origin('https://example.staging.all-hands.dev')
            is True
        )
