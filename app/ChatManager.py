#!/usr/bin/env python
# coding: UTF-8 
# author: Cmoon
# date: 2024/10/13 上午7:40

# chat_manager.py
class ChatManager:
    def __init__(self, database):
        self.db = database

    def get_user_chats(self, user_id):
        return self.db.get_user_chats(user_id)

    def create_chat(self, user_id, title):
        return self.db.create_chat(user_id, title)

    def get_chat(self, chat_id):
        return self.db.get_chat(chat_id)

    def update_chat_title(self, chat_id, title):
        self.db.update_chat_title(chat_id, title)

    def delete_chat(self, chat_id):
        self.db.delete_chat(chat_id)

    def pin_chat(self, chat_id):
        self.db.pin_chat(chat_id)

    def unpin_chat(self, chat_id):
        self.db.unpin_chat(chat_id)

    def get_messages(self, chat_id):
        return self.db.get_messages(chat_id)

    def add_message(self, chat_id, role, content):
        self.db.add_message(chat_id, role, content)
