#!/usr/bin/env python
# coding: UTF-8
# author: Cmoon
# date: 2024/10/4 下午10:10

import streamlit as st
from collections import deque
from openai import OpenAI
import uuid
import logging
from database import Database


class ChatbotUI:
    def __init__(self):
        st.set_page_config(layout="wide")
        self.setup_logging()
        try:
            self.db = Database()
            self.db.init_db()
        except Exception as e:
            st.error(f"数据库连接失败: {e}")
            st.stop()

        if "current_chat_id" not in st.session_state:
            st.session_state.current_chat_id = None

        self.setup_sidebar()
        self.main_content()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def setup_sidebar(self):
        with st.sidebar:
            st.title("🌙 CMoonbot 💬")
            st.caption("🚀 A chatbot made by CMoon")

            chat_tab, settings_tab,raw_tab = st.tabs(["聊天", "设置",'原始输出'])

            with chat_tab:
                if st.button("新建对话", key="new_chat"):
                    new_chat_id = self.new_chat()
                    if new_chat_id:
                        st.session_state.current_chat_id = new_chat_id
                        st.session_state.current_chat_title = "新对话"
                    st.rerun()
                # st.divider()
                st.markdown("## 历史对话")
                try:
                    for chat in self.db.get_chats():
                        title = chat['title'][:18] + "..." if len(chat['title']) > 18 else chat['title']
                        # if chat['id'] == st.session_state.get('current_chat_id'):
                        #     title = st.session_state.get('current_chat_title', title)
                        pin_icon = "📌 " if chat.get('pinned', False) else ""

                        if st.button(f"{pin_icon}📄 {title}", key=chat['id']):
                            st.session_state.current_chat_id = chat['id']
                            st.session_state.current_chat_title = chat['title']
                            st.rerun()
                except Exception as e:
                    self.logger.error(f"获取聊天列表失败: {e}")
                    st.error("获取聊天列表失败，请刷新页面重试。")

            with settings_tab:
                self.setup_model_settings()
                self.setup_api_settings()
                self.setup_parameter_settings()
            with raw_tab:
                self.display_raw_output()
    def main_content(self):
        if st.session_state.current_chat_id:
            try:
                current_chat = self.db.get_chat(st.session_state.current_chat_id)
                if current_chat:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        # 使用 session state 中的标题，如果有的话
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

                    messages = self.db.get_messages(st.session_state.current_chat_id)
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
                    self.db.delete_chat(chat_id)
                    st.session_state.current_chat_id = None
                    # st.success("对话已删除")
                    st.rerun()
            elif operation == "重命名":
                new_title = st.text_input("新标题", key="new_chat_title")
                if st.button("确认重命名"):
                    self.db.update_chat_title(chat_id, new_title)
                    st.success("对话已重命名")
                    st.rerun()
            elif operation == "置顶":
                self.db.pin_chat(chat_id)
                # st.success("对话已置顶")
                st.rerun()
            elif operation == "取消置顶":
                self.db.unpin_chat(chat_id)
                # st.success("已取消置顶")
                st.rerun()
        except Exception as e:
            self.logger.error(f"操作失败: {e}")
            st.error(f"操作失败: {e}")

    def new_chat(self):
        try:
            title = "新对话"  # 临时标题
            new_chat_id = self.db.create_chat(title)
            self.db.add_message(new_chat_id, "system", "How can I help you?")
            return new_chat_id
        except Exception as e:
            self.logger.error(f"创建新对话失败: {e}")
            st.error("创建新对话失败，请重试。")
            return None

    def setup_model_settings(self):
        st.title("模型设置")
        model_options = [
            "gpt-4o", "o1-preview", "claude-3-5-sonnet-20240620",
            "gpt-4-turbo-preview", "gpt-4-vision-preview"
        ]
        st.session_state["openai_model"] = st.selectbox("选择模型", model_options)

    def setup_api_settings(self):
        with st.expander("API设置"):
            st.text_input(
                "OpenAI API Key", key="openai_api_key", type="password",
                value=st.secrets.api_secrets.API_SECRET_KEY
            )
            st.text_input(
                "OpenAI Base URL", key="openai_base_url", type="password",
                value=st.secrets.api_secrets.BASE_URL
            )

    def setup_parameter_settings(self):
        with st.expander("参数调节"):
            st.session_state.memory = st.slider("Memory", min_value=0, max_value=36, value=10, step=1)
            st.session_state.temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
            st.session_state.top_p = st.slider("Top P", min_value=0.0, max_value=1.0, value=0.9, step=0.1)
            st.session_state.max_tokens = st.slider("Max Tokens", min_value=1, max_value=8000, value=2048, step=1)

    def display_raw_output(self):
        if st.session_state.current_chat_id:
            messages = self.db.get_messages(st.session_state.current_chat_id)
            st.write(messages)
        else:
            st.write("No chat selected")

    def display_chat_messages(self, messages):
        for message in messages:
            if message["role"] != "system":
                avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])

    def handle_user_input(self):
        prompt = st.chat_input("在这里输入您的问题...")
        if prompt:
            # try:
            if not st.session_state.current_chat_id:
                # 如果没有当前对话，创建一个新的
                new_chat_id = self.new_chat()
            else:
                new_chat_id = st.session_state.current_chat_id

            st.session_state.current_chat_id = new_chat_id

            # 将用户输入添加到对话
            self.db.add_message(new_chat_id, "user", prompt)


            current_chat = self.db.get_chat(st.session_state.current_chat_id)
            if not current_chat or current_chat['title'] == "新对话":
                new_title = prompt
                self.db.update_chat_title(st.session_state.current_chat_id, new_title)
                st.session_state.current_chat_title = new_title


            # 显示用户输入
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(prompt)

            # 生成并显示AI响应
            model = ChatModel(
                st.session_state.openai_api_key,
                st.session_state.openai_base_url,
                st.session_state["openai_model"]
            )

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("正在思考..."):
                    messages = self.db.get_messages(new_chat_id)
                    response = model.generate_response(messages)

            # 将AI响应添加到数据库
            self.db.add_message(new_chat_id, "assistant", response)




            # 使用 st.experimental_rerun() 来刷新整个应用
            st.rerun()
            # except Exception as e:
            #     self.logger.error(f"处理用户输入失败: {e}")
            #     st.error("处理您的输入时出错，请重试。")


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