#!/usr/bin/env python
# coding: UTF-8 
# author: Cmoon
# date: 2024/10/13 上午7:40

class UserManager:
    def __init__(self, database):
        self.db = database

    def get_user(self, user_id):
        return self.db.get_user_by_id(user_id)

    def update_api_settings(self, user_id, api_key, base_url):
        self.db.update_user_api_settings(user_id, api_key, base_url)

    def get_api_settings(self, user_id):
        user = self.get_user(user_id)
        return user['api_key'], user['base_url']