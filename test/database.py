import unittest
from unittest.mock import patch, MagicMock
from app.database import Database

class TestDatabase(unittest.TestCase):

    @patch('app.database.psycopg2.connect')
    def setUp(self, mock_connect):
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.db = Database()

    def test_init_db(self):
        self.db.init_db()
        self.assertEqual(self.mock_cursor.execute.call_count, 2)
        self.mock_conn.commit.assert_called_once()

    def test_get_chats(self):
        self.db.get_chats()
        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM chats ORDER BY created_at DESC")
        self.mock_cursor.fetchall.assert_called_once()

    def test_get_chat(self):
        chat_id = 'some-uuid'
        self.db.get_chat(chat_id)
        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM chats WHERE id = %s", (chat_id,))
        self.mock_cursor.fetchone.assert_called_once()

    def test_create_chat(self):
        chat_id = 'some-uuid'
        title = 'Test Chat'
        self.db.create_chat(chat_id, title)
        self.mock_cursor.execute.assert_called_once_with("INSERT INTO chats (id, title) VALUES (%s, %s)", (chat_id, title))
        self.mock_conn.commit.assert_called_once()

    def test_update_chat_title(self):
        chat_id = 'some-uuid'
        title = 'Updated Title'
        self.db.update_chat_title(chat_id, title)
        self.mock_cursor.execute.assert_called_once_with("UPDATE chats SET title = %s WHERE id = %s", (title, chat_id))
        self.mock_conn.commit.assert_called_once()

    def test_get_messages(self):
        chat_id = 'some-uuid'
        self.db.get_messages(chat_id)
        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM messages WHERE chat_id = %s ORDER BY created_at", (chat_id,))
        self.mock_cursor.fetchall.assert_called_once()

    def test_add_message(self):
        chat_id = 'some-uuid'
        role = 'user'
        content = 'Hello, world!'
        self.db.add_message(chat_id, role, content)
        self.mock_cursor.execute.assert_called_once_with("INSERT INTO messages (chat_id, role, content) VALUES (%s, %s, %s)", (chat_id, role, content))
        self.mock_conn.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()