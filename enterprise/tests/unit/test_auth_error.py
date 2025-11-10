from server.auth.auth_error import (
    AuthError,
    BearerTokenError,
    CookieError,
    NoCredentialsError,
)


def test_auth_error_inheritance():
    """Test that all auth errors inherit from AuthError."""
    assert issubclass(NoCredentialsError, AuthError)
    assert issubclass(BearerTokenError, AuthError)
    assert issubclass(CookieError, AuthError)


def test_auth_error_instantiation():
    """Test that auth errors can be instantiated."""
    auth_error = AuthError()
    assert isinstance(auth_error, Exception)
    assert isinstance(auth_error, AuthError)


def test_no_auth_provided_error_instantiation():
    """Test that NoCredentialsError can be instantiated."""
    error = NoCredentialsError()
    assert isinstance(error, Exception)
    assert isinstance(error, AuthError)
    assert isinstance(error, NoCredentialsError)


def test_bearer_token_error_instantiation():
    """Test that BearerTokenError can be instantiated."""
    error = BearerTokenError()
    assert isinstance(error, Exception)
    assert isinstance(error, AuthError)
    assert isinstance(error, BearerTokenError)


def test_cookie_error_instantiation():
    """Test that CookieError can be instantiated."""
    error = CookieError()
    assert isinstance(error, Exception)
    assert isinstance(error, AuthError)
    assert isinstance(error, CookieError)


def test_auth_error_with_message():
    """Test that auth errors can be instantiated with a message."""
    error = AuthError('Test error message')
    assert str(error) == 'Test error message'


def test_auth_error_with_cause():
    """Test that auth errors can be instantiated with a cause."""
    cause = ValueError('Original error')
    try:
        raise AuthError('Wrapped error') from cause
    except AuthError as e:
        assert str(e) == 'Wrapped error'
        assert e.__cause__ == cause
