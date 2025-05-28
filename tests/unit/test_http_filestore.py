from __future__ import annotations

import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

from requests.exceptions import RequestException

from openhands.storage.http import HTTPFileStore


class TestHTTPFileStore(TestCase):
    def setUp(self):
        self.base_url = 'https://example.com/api'
        self.api_key = 'test-api-key'
        with patch('requests.Session') as mock_session_class:
            self.mock_session = MagicMock()
            mock_session_class.return_value = self.mock_session
            self.store = HTTPFileStore(self.base_url, api_key=self.api_key)

    def test_init_with_api_key(self):
        self.assertEqual(self.store.base_url, 'https://example.com/api')
        self.assertEqual(self.store.headers, {'X-API-Key': 'test-api-key'})
        self.assertIsNone(self.store.auth)

    def test_init_with_basic_auth(self):
        with patch('requests.Session'):
            store = HTTPFileStore(self.base_url, username='user', password='pass')
            self.assertEqual(store.auth, ('user', 'pass'))
            self.assertEqual(store.headers, {})

    def test_init_with_bearer_token(self):
        with patch('requests.Session'):
            store = HTTPFileStore(self.base_url, bearer_token='token123')
            self.assertEqual(store.headers, {'Authorization': 'Bearer token123'})
            self.assertIsNone(store.auth)

    def test_get_file_url(self):
        url = self.store._get_file_url('/test/path')
        self.assertEqual(url, 'https://example.com/api/files/test/path')

        # Test URL encoding
        url = self.store._get_file_url('/test/path with spaces')
        self.assertEqual(url, 'https://example.com/api/files/test/path%20with%20spaces')

    def test_write_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.mock_session.post.return_value = mock_response

        self.store.write('/test/file.txt', 'Hello, world!')

        self.mock_session.post.assert_called_once_with(
            'https://example.com/api/files/test/file.txt',
            data=b'Hello, world!',
            headers={'X-API-Key': 'test-api-key'},
            auth=None,
            timeout=30,
            verify=True,
        )

    def test_write_failure(self):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = 'Permission denied'
        self.mock_session.post.return_value = mock_response

        with self.assertRaises(FileNotFoundError) as context:
            self.store.write('/test/file.txt', 'Hello, world!')

        self.assertIn('Status code: 403', str(context.exception))
        self.assertIn('Permission denied', str(context.exception))

    def test_write_request_exception(self):
        self.mock_session.post.side_effect = RequestException('Connection error')

        with self.assertRaises(FileNotFoundError) as context:
            self.store.write('/test/file.txt', 'Hello, world!')

        self.assertIn('Connection error', str(context.exception))

    def test_read_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'Hello, world!'
        self.mock_session.get.return_value = mock_response

        result = self.store.read('/test/file.txt')

        self.assertEqual(result, 'Hello, world!')
        self.mock_session.get.assert_called_once_with(
            'https://example.com/api/files/test/file.txt',
            headers={'X-API-Key': 'test-api-key'},
            auth=None,
            timeout=30,
            verify=True,
        )

    def test_read_failure(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'File not found'
        self.mock_session.get.return_value = mock_response

        with self.assertRaises(FileNotFoundError) as context:
            self.store.read('/test/file.txt')

        self.assertIn('Status code: 404', str(context.exception))
        self.assertIn('File not found', str(context.exception))

    def test_list_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ['file1.txt', 'file2.txt', 'dir/']
        self.mock_session.get.return_value = mock_response

        result = self.store.list('/test')

        self.assertEqual(result, ['file1.txt', 'file2.txt', 'dir/'])
        self.mock_session.get.assert_called_once_with(
            'https://example.com/api/files/test/list',
            headers={'X-API-Key': 'test-api-key'},
            auth=None,
            timeout=30,
            verify=True,
        )

    def test_list_empty_directory(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        self.mock_session.get.return_value = mock_response

        result = self.store.list('/test')

        self.assertEqual(result, [])

    def test_list_invalid_json(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError('Invalid JSON', '', 0)
        self.mock_session.get.return_value = mock_response

        with self.assertRaises(FileNotFoundError) as context:
            self.store.list('/test')

        self.assertIn('Invalid JSON response', str(context.exception))

    def test_list_invalid_response_format(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'files': ['file1.txt']}  # Not a list
        self.mock_session.get.return_value = mock_response

        with self.assertRaises(FileNotFoundError) as context:
            self.store.list('/test')

        self.assertIn('Invalid response format', str(context.exception))

    def test_delete_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 204
        self.mock_session.delete.return_value = mock_response

        self.store.delete('/test/file.txt')

        self.mock_session.delete.assert_called_once_with(
            'https://example.com/api/files/test/file.txt',
            headers={'X-API-Key': 'test-api-key'},
            auth=None,
            timeout=30,
            verify=True,
        )

    def test_delete_not_found(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        self.mock_session.delete.return_value = mock_response

        # Should not raise an exception for 404 on delete
        self.store.delete('/test/file.txt')

    def test_delete_failure(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal server error'
        self.mock_session.delete.return_value = mock_response

        with self.assertRaises(FileNotFoundError) as context:
            self.store.delete('/test/file.txt')

        self.assertIn('Status code: 500', str(context.exception))
        self.assertIn('Internal server error', str(context.exception))
