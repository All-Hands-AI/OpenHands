import httpx

from openhands.utils.ensure_httpx_close import ensure_httpx_close


def test_ensure_httpx_close_basic():
    """Test basic functionality of ensure_httpx_close."""
    ctx = ensure_httpx_close()
    with ctx:
        # Create a client - should be tracked
        client = httpx.Client()

    # After context exit, client should be closed
    assert client.is_closed


def test_ensure_httpx_close_multiple_clients():
    """Test ensure_httpx_close with multiple clients."""
    ctx = ensure_httpx_close()
    with ctx:
        client1 = httpx.Client()
        client2 = httpx.Client()

    assert client1.is_closed
    assert client2.is_closed


def test_ensure_httpx_close_nested():
    """Test nested usage of ensure_httpx_close."""
    with ensure_httpx_close():
        client1 = httpx.Client()

        with ensure_httpx_close():
            client2 = httpx.Client()
            assert not client2.is_closed

        # After inner context, client2 should be closed
        assert client2.is_closed
        # client1 should still be open since outer context is still active
        assert not client1.is_closed

    # After outer context, both clients should be closed
    assert client1.is_closed
    assert client2.is_closed


def test_ensure_httpx_close_exception():
    """Test ensure_httpx_close when an exception occurs."""
    client = None
    try:
        with ensure_httpx_close():
            client = httpx.Client()
            raise ValueError('Test exception')
    except ValueError:
        pass

    # Client should be closed even if an exception occurred
    assert client is not None
    assert client.is_closed


def test_ensure_httpx_close_restore_client():
    """Test that the original client is restored after context exit."""
    original_client = httpx.Client
    with ensure_httpx_close():
        assert httpx.Client != original_client

    # Original __init__ should be restored
    assert httpx.Client == original_client
