#!/usr/bin/env python
# coding: UTF-8 
# author: Cmoon
# date: 2024/10/13 上午7:13

from werkzeug.security import generate_password_hash, check_password_hash

class AuthManager:
    def __init__(self, database):
        self.db = database

    def register_user(self, username, password):
        if self.db.get_user(username):
            return None, "用户名已存在"
        password_hash = generate_password_hash(password)
        user_id = self.db.create_user(username, password_hash)
        return user_id, "注册成功"

    def login_user(self, username, password):
        user = self.db.get_user(username)
        if user and check_password_hash(user['password_hash'], password):
            return user['id'], "登录成功"
        return None, "用户名或密码错误"

    def logout_user(self):
        # 这里可以添加任何必要的注销逻辑
        return True


def main():
    main = Main()


if __name__ == '__main__':
    main()
