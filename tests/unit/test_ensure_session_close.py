"""Tests for the session management utilities."""

import pytest

from openhands.utils.ensure_session_close import (
    ensure_aiohttp_close,
    ensure_all_sessions_close,
    ensure_httpx_close,
)


def test_ensure_httpx_close_basic():
    """Test basic functionality of ensure_httpx_close."""
    import httpx

    original_client = httpx.Client

    with ensure_httpx_close():
        # Create a client within the context
        client = httpx.Client()
        assert not client.is_closed

        # Check that the client is a proxy
        assert client.__class__.__name__ == 'ClientProxy'

    # After context, client should be closed
    assert client.is_closed

    # Original class should be restored
    assert httpx.Client is original_client


@pytest.mark.asyncio
async def test_ensure_aiohttp_close_basic():
    """Test basic functionality of ensure_aiohttp_close."""
    import aiohttp

    original_session = aiohttp.ClientSession
    sessions_created = []

    async with ensure_aiohttp_close():
        # Create sessions within the context
        session1 = aiohttp.ClientSession()
        session2 = aiohttp.ClientSession()
        sessions_created = [session1, session2]

        assert not session1.closed
        assert not session2.closed

        # Check that the sessions are using the proxy
        assert session1.__class__.__name__ == 'SessionProxy'
        assert session2.__class__.__name__ == 'SessionProxy'

    # After context, sessions should be closed
    for session in sessions_created:
        assert session.closed

    # Original class should be restored
    assert aiohttp.ClientSession is original_session


@pytest.mark.asyncio
async def test_ensure_all_sessions_close():
    """Test combined session management."""
    import aiohttp
    import httpx

    original_aiohttp_session = aiohttp.ClientSession
    original_httpx_client = httpx.Client

    async with ensure_all_sessions_close():
        # Create both types of clients
        aiohttp_session = aiohttp.ClientSession()
        httpx_client = httpx.Client()

        assert not aiohttp_session.closed
        assert not httpx_client.is_closed

    # After context, both should be closed
    assert aiohttp_session.closed
    assert httpx_client.is_closed

    # Original classes should be restored
    assert aiohttp.ClientSession is original_aiohttp_session
    assert httpx.Client is original_httpx_client


def test_ensure_httpx_close_reusable():
    """Test that proxied clients can be reused after closing."""
    import httpx

    with ensure_httpx_close():
        client = httpx.Client()
        client.close()

        # Should be able to use the client again
        assert client.is_closed
        # Accessing a method should recreate the underlying client
        _ = client.timeout  # This should recreate the client
        assert not client.is_closed
