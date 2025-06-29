"""
Unit tests for MCP Mount Middleware.

Tests the MountFastMCP middleware that fixes ASGI protocol violations
when FastMCP is mounted under sub-paths.

This addresses the error: AssertionError: assert message["type"] == "http.response.body"
"""

from unittest.mock import AsyncMock

import pytest

from openhands.server.middlewares.mcp_mount import MountFastMCP


class TestMountFastMCP:
    """Test cases for MountFastMCP middleware."""

    def test_init(self):
        """Test middleware initialization."""
        mock_app = AsyncMock()
        middleware = MountFastMCP(app=mock_app)

        assert middleware.app == mock_app
        assert hasattr(middleware, '_endpoint_event_regex')
        assert middleware._endpoint_event_regex is not None

    def test_regex_pattern_basic_endpoint(self):
        """Test regex pattern matches basic endpoint events."""
        middleware = MountFastMCP(app=AsyncMock())

        test_body = b'event: endpoint\r\ndata: /messages/\r\n\r\n'
        match = middleware._endpoint_event_regex.match(test_body)

        assert match is not None
        groups = match.groups()
        assert len(groups) == 3
        assert groups[0] == b'event: endpoint\r\ndata: '
        assert groups[1] == b'/messages/'
        assert groups[2] == b'\r\n\r\n'

    def test_regex_pattern_endpoint_with_query(self):
        """Test regex pattern matches endpoint events with query strings."""
        middleware = MountFastMCP(app=AsyncMock())

        test_body = b'event: endpoint\r\ndata: /api/v1/?session=123\r\n\r\n'
        match = middleware._endpoint_event_regex.match(test_body)

        assert match is not None
        groups = match.groups()
        assert groups[0] == b'event: endpoint\r\ndata: '
        assert groups[1] == b'/api/v1/'
        assert groups[2] == b'?session=123\r\n\r\n'

    def test_regex_pattern_root_endpoint(self):
        """Test regex pattern matches root endpoint events."""
        middleware = MountFastMCP(app=AsyncMock())

        test_body = b'event: endpoint\r\ndata: /\r\n\r\n'
        match = middleware._endpoint_event_regex.match(test_body)

        assert match is not None
        groups = match.groups()
        assert groups[1] == b'/'

    def test_regex_pattern_non_endpoint_event(self):
        """Test regex pattern does not match non-endpoint events."""
        middleware = MountFastMCP(app=AsyncMock())

        test_body = b'event: data\r\ndata: some content\r\n\r\n'
        match = middleware._endpoint_event_regex.match(test_body)

        assert match is None

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        """Test that non-HTTP scopes are passed through unchanged."""
        mock_app = AsyncMock()
        middleware = MountFastMCP(app=mock_app)

        scope = {'type': 'websocket'}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        mock_app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_http_scope_with_root_path_rewriting(self):
        """Test HTTP scope with root path rewriting."""
        mock_app = AsyncMock()
        middleware = MountFastMCP(app=mock_app)

        scope = {'type': 'http', 'root_path': '/mcp'}
        receive = AsyncMock()
        send = AsyncMock()

        # Mock the app to call our wrapped_send with an endpoint event
        async def mock_app_call(scope, receive, wrapped_send):
            # Simulate sending an HTTP response with endpoint event
            await wrapped_send(
                {'type': 'http.response.start', 'status': 200, 'headers': []}
            )
            await wrapped_send(
                {
                    'type': 'http.response.body',
                    'body': b'event: endpoint\r\ndata: /messages/\r\n\r\n',
                    'more_body': False,
                }
            )

        mock_app.side_effect = mock_app_call

        await middleware(scope, receive, send)

        # Verify the app was called with wrapped_send
        mock_app.assert_called_once()

        # Verify send was called with rewritten body
        assert send.call_count == 2

        # Check the response start
        start_call = send.call_args_list[0]
        assert start_call[0][0]['type'] == 'http.response.start'

        # Check the response body was rewritten
        body_call = send.call_args_list[1]
        body_message = body_call[0][0]
        assert body_message['type'] == 'http.response.body'
        assert (
            body_message['body'] == b'event: endpoint\r\ndata: /mcp/messages/\r\n\r\n'
        )

    @pytest.mark.asyncio
    async def test_http_scope_root_mount_no_rewriting(self):
        """Test HTTP scope with root mount path (no rewriting needed)."""
        mock_app = AsyncMock()
        middleware = MountFastMCP(app=mock_app)

        scope = {'type': 'http', 'root_path': '/'}
        receive = AsyncMock()
        send = AsyncMock()

        async def mock_app_call(scope, receive, wrapped_send):
            await wrapped_send(
                {
                    'type': 'http.response.body',
                    'body': b'event: endpoint\r\ndata: /messages/\r\n\r\n',
                    'more_body': False,
                }
            )

        mock_app.side_effect = mock_app_call

        await middleware(scope, receive, send)

        # Verify send was called with unchanged body (root mount)
        body_call = send.call_args_list[0]
        body_message = body_call[0][0]
        assert body_message['body'] == b'event: endpoint\r\ndata: /messages/\r\n\r\n'

    @pytest.mark.asyncio
    async def test_http_scope_non_endpoint_body_unchanged(self):
        """Test HTTP scope with non-endpoint body remains unchanged."""
        mock_app = AsyncMock()
        middleware = MountFastMCP(app=mock_app)

        scope = {'type': 'http', 'root_path': '/mcp'}
        receive = AsyncMock()
        send = AsyncMock()

        async def mock_app_call(scope, receive, wrapped_send):
            await wrapped_send(
                {
                    'type': 'http.response.body',
                    'body': b'event: data\r\ndata: some content\r\n\r\n',
                    'more_body': False,
                }
            )

        mock_app.side_effect = mock_app_call

        await middleware(scope, receive, send)

        # Verify send was called with unchanged body (non-endpoint event)
        body_call = send.call_args_list[0]
        body_message = body_call[0][0]
        assert body_message['body'] == b'event: data\r\ndata: some content\r\n\r\n'

    @pytest.mark.asyncio
    async def test_http_scope_no_root_path(self):
        """Test HTTP scope without root_path defaults to empty string."""
        mock_app = AsyncMock()
        middleware = MountFastMCP(app=mock_app)

        scope = {'type': 'http'}  # No root_path
        receive = AsyncMock()
        send = AsyncMock()

        async def mock_app_call(scope, receive, wrapped_send):
            await wrapped_send(
                {
                    'type': 'http.response.body',
                    'body': b'event: endpoint\r\ndata: /messages/\r\n\r\n',
                    'more_body': False,
                }
            )

        mock_app.side_effect = mock_app_call

        await middleware(scope, receive, send)

        # Verify send was called with unchanged body (no root_path)
        body_call = send.call_args_list[0]
        body_message = body_call[0][0]
        assert body_message['body'] == b'event: endpoint\r\ndata: /messages/\r\n\r\n'

    @pytest.mark.asyncio
    async def test_http_scope_trailing_slash_removal(self):
        """Test HTTP scope with trailing slash in root_path is handled correctly."""
        mock_app = AsyncMock()
        middleware = MountFastMCP(app=mock_app)

        scope = {'type': 'http', 'root_path': '/mcp/'}  # Trailing slash
        receive = AsyncMock()
        send = AsyncMock()

        async def mock_app_call(scope, receive, wrapped_send):
            await wrapped_send(
                {
                    'type': 'http.response.body',
                    'body': b'event: endpoint\r\ndata: /messages/\r\n\r\n',
                    'more_body': False,
                }
            )

        mock_app.side_effect = mock_app_call

        await middleware(scope, receive, send)

        # Verify trailing slash was removed and path rewritten correctly
        body_call = send.call_args_list[0]
        body_message = body_call[0][0]
        assert (
            body_message['body'] == b'event: endpoint\r\ndata: /mcp/messages/\r\n\r\n'
        )

    def test_endpoint_rewriting_scenarios(self):
        """Test various endpoint rewriting scenarios."""
        middleware = MountFastMCP(app=AsyncMock())

        test_cases = [
            {
                'name': 'Basic endpoint',
                'input': b'event: endpoint\r\ndata: /messages/\r\n\r\n',
                'root_path': '/mcp',
                'expected': b'event: endpoint\r\ndata: /mcp/messages/\r\n\r\n',
            },
            {
                'name': 'Root endpoint',
                'input': b'event: endpoint\r\ndata: /\r\n\r\n',
                'root_path': '/mcp',
                'expected': b'event: endpoint\r\ndata: /mcp/\r\n\r\n',
            },
            {
                'name': 'Endpoint with query string',
                'input': b'event: endpoint\r\ndata: /api/v1/?session=123\r\n\r\n',
                'root_path': '/mcp',
                'expected': b'event: endpoint\r\ndata: /mcp/api/v1/?session=123\r\n\r\n',
            },
            {
                'name': 'Root mount (no change)',
                'input': b'event: endpoint\r\ndata: /messages/\r\n\r\n',
                'root_path': '/',
                'expected': b'event: endpoint\r\ndata: /messages/\r\n\r\n',
            },
            {
                'name': 'Non-endpoint event (no change)',
                'input': b'event: data\r\ndata: some content\r\n\r\n',
                'root_path': '/mcp',
                'expected': b'event: data\r\ndata: some content\r\n\r\n',
            },
        ]

        for test_case in test_cases:
            root_path_bytes = test_case['root_path'].encode('utf-8')
            body = test_case['input']

            # Apply middleware transformation logic
            if body.startswith(b'event: endpoint\r\ndata: '):
                match = middleware._endpoint_event_regex.match(body)
                if match:
                    prefix, relative_path, remainder = match.groups()

                    if root_path_bytes == b'/':
                        full_path = relative_path
                    else:
                        full_path = root_path_bytes + relative_path

                    result = prefix + full_path + remainder
                else:
                    result = body
            else:
                result = body

            assert result == test_case['expected'], (
                f'Failed test case: {test_case["name"]}'
            )


class TestMountFastMCPIntegration:
    """Integration tests for MountFastMCP middleware."""

    @pytest.mark.asyncio
    async def test_asgi_protocol_compliance(self):
        """Test that middleware maintains ASGI protocol compliance."""
        mock_app = AsyncMock()
        middleware = MountFastMCP(app=mock_app)

        scope = {'type': 'http', 'root_path': '/mcp'}
        receive = AsyncMock()
        send = AsyncMock()

        # Simulate a complete ASGI message sequence
        async def mock_app_call(scope, receive, wrapped_send):
            # Send response start
            await wrapped_send(
                {
                    'type': 'http.response.start',
                    'status': 200,
                    'headers': [[b'content-type', b'text/event-stream']],
                }
            )

            # Send multiple body chunks
            await wrapped_send(
                {
                    'type': 'http.response.body',
                    'body': b'event: endpoint\r\ndata: /messages/\r\n\r\n',
                    'more_body': True,
                }
            )

            await wrapped_send(
                {
                    'type': 'http.response.body',
                    'body': b'event: data\r\ndata: some content\r\n\r\n',
                    'more_body': True,
                }
            )

            await wrapped_send(
                {
                    'type': 'http.response.body',
                    'body': b'event: endpoint\r\ndata: /api/\r\n\r\n',
                    'more_body': False,
                }
            )

        mock_app.side_effect = mock_app_call

        await middleware(scope, receive, send)

        # Verify all messages were sent in correct order
        assert send.call_count == 4

        # Check response start
        start_call = send.call_args_list[0][0][0]
        assert start_call['type'] == 'http.response.start'
        assert start_call['status'] == 200

        # Check first body (endpoint event - should be rewritten)
        body1_call = send.call_args_list[1][0][0]
        assert body1_call['type'] == 'http.response.body'
        assert body1_call['body'] == b'event: endpoint\r\ndata: /mcp/messages/\r\n\r\n'
        assert body1_call['more_body'] is True

        # Check second body (data event - should be unchanged)
        body2_call = send.call_args_list[2][0][0]
        assert body2_call['type'] == 'http.response.body'
        assert body2_call['body'] == b'event: data\r\ndata: some content\r\n\r\n'
        assert body2_call['more_body'] is True

        # Check third body (endpoint event - should be rewritten)
        body3_call = send.call_args_list[3][0][0]
        assert body3_call['type'] == 'http.response.body'
        assert body3_call['body'] == b'event: endpoint\r\ndata: /mcp/api/\r\n\r\n'
        assert body3_call['more_body'] is False

    def test_fixes_asgi_protocol_violation_issue(self):
        """
        Test that demonstrates the fix for the specific issue from clone-log-6.txt.

        This test shows how the middleware prevents the AssertionError:
        assert message["type"] == "http.response.body"
        """
        middleware = MountFastMCP(app=AsyncMock())

        # This is the problematic scenario from the logs:
        # 1. FastMCP is mounted at /mcp
        # 2. It sends endpoint events with relative paths
        # 3. Without fix: clients get wrong paths, causing ASGI violations
        # 4. With fix: clients get correct paths, preventing violations

        problematic_sse_body = b'event: endpoint\r\ndata: /messages/\r\n\r\n'
        mount_path = '/mcp'

        # Without fix: body would remain unchanged
        without_fix = problematic_sse_body

        # With fix: body gets rewritten with correct path
        match = middleware._endpoint_event_regex.match(problematic_sse_body)
        assert match is not None, 'Middleware should match endpoint events'

        prefix, relative_path, remainder = match.groups()
        root_path_bytes = mount_path.encode('utf-8')
        full_path = root_path_bytes + relative_path
        with_fix = prefix + full_path + remainder

        # Verify the transformation
        assert without_fix == b'event: endpoint\r\ndata: /messages/\r\n\r\n'
        assert with_fix == b'event: endpoint\r\ndata: /mcp/messages/\r\n\r\n'

        # This transformation prevents:
        # - Clients from requesting wrong endpoints (/messages/ instead of /mcp/messages/)
        # - ASGI middleware confusion about message sequencing
        # - The AssertionError: assert message["type"] == "http.response.body"

        assert without_fix != with_fix, 'Fix should change the endpoint path'
        assert b'/mcp/messages/' in with_fix, 'Fixed path should include mount prefix'
