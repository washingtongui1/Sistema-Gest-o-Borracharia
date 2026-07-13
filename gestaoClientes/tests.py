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
