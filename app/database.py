#!/usr/bin/env python
# coding: UTF-8 
# author: Cmoon
# date: 2024/10/10 下午9:39

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import uuid

class Database:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.setup_logging()
        self.connect()

    def __del__(self):
        self.close()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def connect(self):
        try:
            self.conn = psycopg2.connect(os.environ['DATABASE_URL'])
            self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
            self.logger.info("Database connection established")
        except psycopg2.Error as e:
            self.logger.error(f"Error connecting to database: {e}")
            raise

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")

    def execute_query(self, query, params=None):
        try:
            self.cur.execute(query, params)
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            self.logger.error(f"Query execution error: {e}")
            raise

    def fetch_one(self, query, params=None):
        self.execute_query(query, params)
        return self.cur.fetchone()

    def fetch_all(self, query, params=None):
        self.execute_query(query, params)
        return self.cur.fetchall()

    def init_db(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS chats (
                id UUID PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pinned BOOLEAN DEFAULT FALSE,
                pinned_at TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                chat_id UUID REFERENCES chats(id),
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        for query in queries:
            self.execute_query(query)
        self.logger.info("Database initialized")

    def get_chats(self):
        query = """
            SELECT id, title, created_at, 
                   COALESCE(pinned, FALSE) as pinned, 
                   pinned_at
            FROM chats 
            ORDER BY COALESCE(pinned, FALSE) DESC, 
                     COALESCE(pinned_at, created_at) DESC, 
                     created_at DESC
        """
        return self.fetch_all(query)

    def get_chat(self, chat_id):
        query = "SELECT * FROM chats WHERE id = %s"
        return self.fetch_one(query, (chat_id,))

    def create_chat(self, title):
        chat_id = str(uuid.uuid4())
        query = "INSERT INTO chats (id, title) VALUES (%s, %s)"
        self.execute_query(query, (chat_id, title))
        return chat_id

    def update_chat_title(self, chat_id, title):
        query = "UPDATE chats SET title = %s WHERE id = %s"
        self.execute_query(query, (title, chat_id))

    def delete_chat(self, chat_id):
        queries = [
            "DELETE FROM messages WHERE chat_id = %s",
            "DELETE FROM chats WHERE id = %s"
        ]
        for query in queries:
            self.execute_query(query, (chat_id,))

    def pin_chat(self, chat_id):
        query = "UPDATE chats SET pinned = TRUE, pinned_at = CURRENT_TIMESTAMP WHERE id = %s"
        self.execute_query(query, (chat_id,))

    def unpin_chat(self, chat_id):
        query = "UPDATE chats SET pinned = FALSE, pinned_at = NULL WHERE id = %s"
        self.execute_query(query, (chat_id,))

    def get_messages(self, chat_id):
        query = "SELECT * FROM messages WHERE chat_id = %s ORDER BY created_at"
        return self.fetch_all(query, (chat_id,))

    def add_message(self, chat_id, role, content):
        query = "INSERT INTO messages (chat_id, role, content) VALUES (%s, %s, %s)"
        self.execute_query(query, (chat_id, role, content))

    def delete_message(self, message_id):
        query = "DELETE FROM messages WHERE id = %s"
        self.execute_query(query, (message_id,))
