from httpx import Client

from openhands.utils.ensure_httpx_close import EnsureHttpxClose


def test_ensure_httpx_close_basic():
    """Test basic functionality of EnsureHttpxClose."""
    clients = []
    ctx = EnsureHttpxClose()
    with ctx:
        # Create a client - should be tracked
        client = Client()
        assert client in ctx.clients
        assert len(ctx.clients) == 1
        clients.append(client)

    # After context exit, client should be closed
    assert client.is_closed


def test_ensure_httpx_close_multiple_clients():
    """Test EnsureHttpxClose with multiple clients."""
    ctx = EnsureHttpxClose()
    with ctx:
        client1 = Client()
        client2 = Client()
        assert len(ctx.clients) == 2
        assert client1 in ctx.clients
        assert client2 in ctx.clients

    assert client1.is_closed
    assert client2.is_closed


def test_ensure_httpx_close_nested():
    """Test nested usage of EnsureHttpxClose."""
    outer_ctx = EnsureHttpxClose()
    with outer_ctx:
        client1 = Client()
        assert client1 in outer_ctx.clients

        inner_ctx = EnsureHttpxClose()
        with inner_ctx:
            client2 = Client()
            assert client2 in inner_ctx.clients
            # Since both contexts are using the same monkey-patched __init__,
            # both contexts will track all clients created while they are active
            assert client2 in outer_ctx.clients

        # After inner context, client2 should be closed
        assert client2.is_closed
        # client1 should still be open since outer context is still active
        assert not client1.is_closed

    # After outer context, both clients should be closed
    assert client1.is_closed
    assert client2.is_closed


def test_ensure_httpx_close_exception():
    """Test EnsureHttpxClose when an exception occurs."""
    client = None
    ctx = EnsureHttpxClose()
    try:
        with ctx:
            client = Client()
            raise ValueError('Test exception')
    except ValueError:
        pass

    # Client should be closed even if an exception occurred
    assert client is not None
    assert client.is_closed


def test_ensure_httpx_close_restore_init():
    """Test that the original __init__ is restored after context exit."""
    original_init = Client.__init__
    ctx = EnsureHttpxClose()
    with ctx:
        assert Client.__init__ != original_init

    # Original __init__ should be restored
    assert Client.__init__ == original_init
