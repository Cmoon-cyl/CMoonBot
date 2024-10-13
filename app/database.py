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
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                api_key TEXT,
                base_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS chats (
                id UUID PRIMARY KEY,
                user_id UUID REFERENCES users(id),
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
        self.add_missing_columns()
        self.check_table_structure()

    def check_table_structure(self):
        tables = ['users', 'chats', 'messages']
        for table in tables:
            query = f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
            """
            columns = self.fetch_all(query)
            self.logger.info(f"Table {table} structure:")
            for column in columns:
                self.logger.info(f"  {column['column_name']} ({column['data_type']})")

    def add_missing_columns(self):
        queries = [
            "ALTER TABLE chats ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id)",
        ]
        for query in queries:
            try:
                self.execute_query(query)
                self.logger.info(f"Executed query: {query}")
            except psycopg2.Error as e:
                self.logger.error(f"Error executing query {query}: {e}")

    def create_user(self, username, password_hash):
        user_id = str(uuid.uuid4())
        query = "INSERT INTO users (id, username, password_hash) VALUES (%s, %s, %s)"
        self.execute_query(query, (user_id, username, password_hash))
        return user_id

    def get_user(self, username):
        query = "SELECT * FROM users WHERE username = %s"
        return self.fetch_one(query, (username,))

    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE id = %s"
        return self.fetch_one(query, (user_id,))

    def update_user_api_settings(self, user_id, api_key, base_url):
        query = "UPDATE users SET api_key = %s, base_url = %s WHERE id = %s"
        self.execute_query(query, (api_key, base_url, user_id))

    def get_user_chats(self, user_id):
        query = """
            SELECT id, title, created_at, 
                   COALESCE(pinned, FALSE) as pinned, 
                   pinned_at
            FROM chats 
            WHERE user_id = %s
            ORDER BY COALESCE(pinned, FALSE) DESC, 
                     COALESCE(pinned_at, created_at) DESC, 
                     created_at DESC
        """
        return self.fetch_all(query, (user_id,))

    def create_chat(self, user_id, title):
        chat_id = str(uuid.uuid4())
        query = "INSERT INTO chats (id, user_id, title) VALUES (%s, %s, %s)"
        self.execute_query(query, (chat_id, user_id, title))
        return chat_id

    def get_chat(self, chat_id):
        query = "SELECT * FROM chats WHERE id = %s"
        return self.fetch_one(query, (chat_id,))

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