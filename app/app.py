#!/usr/bin/env python
# coding: UTF-8
# author: Cmoon
# date: 2024/10/4 下午10:10

import streamlit as st
from database import Database
from AuthManager import AuthManager
from UserManager import UserManager
from ChatManager import ChatManager
from openai import OpenAI
import logging


class ChatbotUI:
    def __init__(self):
        st.set_page_config(layout="wide")
        self.setup_logging()

        try:
            self.db = Database()
            self.db.init_db()
            self.auth_manager = AuthManager(self.db)
            self.user_manager = UserManager(self.db)
            self.chat_manager = ChatManager(self.db)
        except Exception as e:
            st.error(f"初始化失败: {e}")
            st.stop()

        if "user_id" not in st.session_state:
            st.session_state.user_id = None
        if "current_chat_id" not in st.session_state:
            st.session_state.current_chat_id = None

        if not st.session_state.user_id:
            self.show_login_register_dialog()
        else:
            self.setup_sidebar()
            self.main_content()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    @st.dialog("登录/注册")
    def show_login_register_dialog(self):

        tab1, tab2 = st.tabs(["登录", "注册"])

        with tab1:
            username = st.text_input("用户名", key="login_username")
            password = st.text_input("密码", type="password", key="login_password")
            if st.button("登录"):
                user_id, message = self.auth_manager.login_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        with tab2:
            new_username = st.text_input("新用户名", key="register_username")
            new_password = st.text_input("新密码", type="password", key="register_password")
            if st.button("注册"):
                user_id, message = self.auth_manager.register_user(new_username, new_password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    def setup_sidebar(self):
        with st.sidebar:
            st.title("🌙 CMoonbot 💬")
            st.caption("🚀 A chatbot made by CMoon")

            chat_tab, settings_tab, raw_tab = st.tabs(["聊天", "设置", '原始输出'])

            with chat_tab:
                if st.button("新建对话", key="new_chat"):
                    new_chat_id = self.chat_manager.create_chat(st.session_state.user_id, "新对话")
                    if new_chat_id:
                        st.session_state.current_chat_id = new_chat_id
                        st.session_state.current_chat_title = "新对话"
                    st.rerun()

                st.markdown("## 历史对话")
                for chat in self.chat_manager.get_user_chats(st.session_state.user_id):
                    title = chat['title'][:18] + "..." if len(chat['title']) > 18 else chat['title']
                    pin_icon = "📌 " if chat.get('pinned', False) else ""
                    if st.button(f"{pin_icon}📄 {title}", key=chat['id']):
                        st.session_state.current_chat_id = chat['id']
                        st.session_state.current_chat_title = chat['title']
                        st.rerun()

            with settings_tab:
                self.setup_model_settings()
                self.setup_api_settings()
                self.setup_parameter_settings()

            with raw_tab:
                self.display_raw_output()

    def setup_model_settings(self):
        st.title("模型设置")
        model_options = [
            "gpt-4o", "o1-preview", "claude-3-5-sonnet-20240620",
            "gpt-4-turbo-preview", "gpt-4-vision-preview"
        ]
        st.session_state["openai_model"] = st.selectbox("选择模型", model_options)

    def setup_api_settings(self):
        with st.expander("API设置"):
            api_key, base_url = self.user_manager.get_api_settings(st.session_state.user_id)
            new_api_key = st.text_input("OpenAI API Key", value=api_key, type="password")
            new_base_url = st.text_input("OpenAI Base URL", value=base_url, type="password")
            if st.button("保存API设置"):
                self.user_manager.update_api_settings(st.session_state.user_id, new_api_key, new_base_url)
                st.success("API设置已更新")

    def setup_parameter_settings(self):
        with st.expander("参数调节"):
            st.session_state.memory = st.slider("Memory", min_value=0, max_value=36, value=10, step=1)
            st.session_state.temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
            st.session_state.top_p = st.slider("Top P", min_value=0.0, max_value=1.0, value=0.9, step=0.1)
            st.session_state.max_tokens = st.slider("Max Tokens", min_value=1, max_value=8000, value=2048, step=1)

    def display_raw_output(self):
        if st.session_state.current_chat_id:
            messages = self.chat_manager.get_messages(st.session_state.current_chat_id)
            st.write(messages)
        else:
            st.write("No chat selected")

    def main_content(self):
        if st.session_state.current_chat_id:
            try:
                current_chat = self.chat_manager.get_chat(st.session_state.current_chat_id)
                if current_chat:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        title = st.session_state.get('current_chat_title', current_chat['title'])
                        st.title(title)
                    with col2:
                        pin_option = "取消置顶" if current_chat.get('pinned', False) else "置顶"
                        operation = st.selectbox(
                            "",
                            ("选择操作", "删除", "重命名", pin_option),
                            key="chat_operation"
                        )
                        if operation != "选择操作":
                            self.handle_chat_operation(operation, current_chat['id'])

                    messages = self.chat_manager.get_messages(st.session_state.current_chat_id)
                    self.display_chat_messages(messages)
            except Exception as e:
                self.logger.error(f"获取当前聊天信息失败: {e}")
                st.error("获取聊天信息失败，请刷新页面重试。")
        else:
            st.title("欢迎使用 CMoonbot")
            st.write("请输入您的问题开始新的对话。")

        self.handle_user_input()

    def handle_chat_operation(self, operation, chat_id):
        try:
            if operation == "删除":
                if st.button("确认删除"):
                    self.chat_manager.delete_chat(chat_id)
                    st.session_state.current_chat_id = None
                    st.rerun()
            elif operation == "重命名":
                new_title = st.text_input("新标题", key="new_chat_title")
                if st.button("确认重命名"):
                    self.chat_manager.update_chat_title(chat_id, new_title)
                    st.success("对话已重命名")
                    st.rerun()
            elif operation == "置顶":
                self.chat_manager.pin_chat(chat_id)
                st.rerun()
            elif operation == "取消置顶":
                self.chat_manager.unpin_chat(chat_id)
                st.rerun()
        except Exception as e:
            self.logger.error(f"操作失败: {e}")
            st.error(f"操作失败: {e}")

    def display_chat_messages(self, messages):
        for message in messages:
            if message["role"] != "system":
                avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])

    def handle_user_input(self):
        prompt = st.chat_input("在这里输入您的问题...")
        if prompt:
            if not st.session_state.current_chat_id:
                new_chat_id = self.chat_manager.create_chat(st.session_state.user_id, "新对话")
                st.session_state.current_chat_id = new_chat_id

            self.chat_manager.add_message(st.session_state.current_chat_id, "user", prompt)

            current_chat = self.chat_manager.get_chat(st.session_state.current_chat_id)
            if current_chat['title'] == "新对话":
                new_title = prompt[:30]
                self.chat_manager.update_chat_title(st.session_state.current_chat_id, new_title)
                st.session_state.current_chat_title = new_title

            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(prompt)

            api_key, base_url = self.user_manager.get_api_settings(st.session_state.user_id)
            model = ChatModel(api_key, base_url, st.session_state["openai_model"])

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("正在思考..."):
                    messages = self.chat_manager.get_messages(st.session_state.current_chat_id)
                    response = model.generate_response(messages)

            self.chat_manager.add_message(st.session_state.current_chat_id, "assistant", response)

            st.rerun()


class ChatModel:
    def __init__(self, api_key, base_url, model):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate_response(self, messages):
        if self.model == "o1-preview":
            return self.generate_o1_response(messages)
        else:
            return self.generate_standard_response(messages)

    def generate_standard_response(self, messages):
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in messages if m["role"] != "system"
            ],
            stream=True,
            max_tokens=st.session_state.max_tokens,
            temperature=st.session_state.temperature,
            top_p=st.session_state.top_p,
        )
        return st.write_stream(stream)

    def generate_o1_response(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user" if m["role"] != "assistant" else "assistant", "content": m["content"]}
                for m in messages if m["role"] != "system"
            ],
            stream=False,
        )
        return response.choices[0].message.content

if __name__ == "__main__":
    ui = ChatbotUI()