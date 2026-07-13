import os
from unittest.mock import patch

from django.test import SimpleTestCase

from gestaoClientes import views


class DbConnectionHelpersTests(SimpleTestCase):
    @patch.dict(os.environ, {
        'DB_HOST': 'server.database.windows.net',
        'DB_NAME': 'db',
        'DB_USER': 'user',
        'DB_PASSWORD': 'pwd',
        'DB_PORT': '1433',
    }, clear=False)
    def test_connection_string_includes_pooling_and_timeout(self):
        conn_str = views._get_connection_string()

        self.assertIn('Pooling=True', conn_str)
        self.assertIn('Connect Timeout=30', conn_str)

    def test_open_connection_returns_single_connection_per_request_flow(self):
        class FakeCursor:
            def close(self):
                return None

        class FakeConnection:
            def cursor(self):
                return FakeCursor()

        with patch.object(views.pyodbc, 'connect', return_value=FakeConnection()) as connect_mock:
            conn, cursor = views._open_connection()

        self.assertEqual(connect_mock.call_count, 1)
        self.assertIsNotNone(conn)
        self.assertIsNotNone(cursor)
