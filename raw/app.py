# Version 2 front end
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from agent import get_llm_and_agent as agentV1
# from retrievalMCP.models import models

import warnings

warnings.filterwarnings("ignore")

# === THIẾT LẬP TRANG WEB ===
def setup_page():
    """
    Cấu hình giao diện trang web
    """
    st.set_page_config(
        page_title="Law Assistant",
        page_icon="🎓",
        layout="wide"
    )

# === KHỞI TẠO ỨNG DỤNG ===
def initialize_app():
    """
    Khởi tạo ứng dụng, bao gồm các biến và giao diện
    """
    setup_page()

    # Khởi tạo danh sách lịch sử trò chuyện
    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories = []

    # Khởi tạo lịch sử tin nhắn hiện tại
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Tôi có thể giúp gì cho bạn?"}
        ]

# === THANH CÔNG CỤ BÊN TRÁI ===
def setup_sidebar():
    """
    Tạo thanh công cụ bên trái với các tùy chọn
    """
    with st.sidebar:
        st.title("⚙️ Cấu hình")
        st.header("🎓 Trợ Lý HRM Innotech Việt Nam")
        st.markdown(
            """
            Hệ thống hỗ trợ tra cứu thông tin HR Innotech Việt Nam.
            - **Mục đích**: Cung cấp thông tin về tuyển dụng, phúc lợi, quy trình làm việc và các vấn đề liên quan đến nhân sự.

            """
        )

        # Nút tạo mới cuộc trò chuyện
        if st.button("🆕 New Chat"):
            if st.session_state.messages:
                st.session_state.chat_histories.append(st.session_state.messages)
            st.session_state.messages = [
                {"role": "assistant", "content": "Tôi có thể giúp gì cho bạn?"}
            ]
            
            st.session_state.reset_msgs = True
            st.success("Cuộc trò chuyện mới đã được tạo!")

# === HIỂN THỊ LỊCH SỬ TRÒ CHUYỆN ===
def show_chat_histories():
    """
    Hiển thị danh sách lịch sử các cuộc trò chuyện
    """
    st.header("📜 Lịch sử cuộc trò chuyện")
    if st.session_state.chat_histories:
        for i, chat in enumerate(st.session_state.chat_histories):
            with st.expander(f"Cuộc trò chuyện {i+1}"):
                for msg in chat:
                    role = "👤 Người dùng" if msg["role"] == "human" else "🤖 AI"
                    st.markdown(f"**{role}:** {msg['content']}")
    else:
        st.write("Chưa có lịch sử cuộc trò chuyện nào.")

def setup_chat_interface():
    st.title("💬 AI Assistant")
    
    # Caption động theo model
    
    st.caption("🚀 Trợ lý AI về Luật")
    
    
    msgs = StreamlitChatMessageHistory(key="langchain_messages")
    
    if st.session_state.get("reset_msgs"):
        msgs.clear()  # Reset lịch sử tin nhắn trong LangChain
        st.session_state.reset_msgs = False
        
        
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Tôi có thể giúp gì cho bạn?"}
        ]
        msgs.add_ai_message("Tôi có thể giúp gì cho bạn?")

    for msg in st.session_state.messages:
        role = "assistant" if msg["role"] == "assistant" else "human"
        st.chat_message(role).write(msg["content"])
        
    return msgs

# === XỬ LÝ TIN NHẮN NGƯỜI DÙNG ===
def handle_user_input(prompt, msgs, agent_executor):
    """
    Xử lý khi người dùng gửi tin nhắn:
    1. Hiển thị tin nhắn người dùng
    2. Gọi AI xử lý và trả lời
    3. Lưu vào lịch sử chat
    """
    
    
    st.session_state.messages.append({"role": "human", "content": prompt})
    st.chat_message("human").write(prompt)
    msgs.add_user_message(prompt)

    # Xử lý và hiển thị câu trả lời
    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        
        # Lấy lịch sử chat để cùng với prompt tạo thành 1 context. 
        chat_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.messages[:-1]
        ]

        # Gọi AI xử lý
        response = agent_executor.invoke(
            {
                "input": prompt,
                "chat_history": chat_history
            },
            {"callbacks": [st_callback]}
        )

        # Lưu và hiển thị câu trả lời
        output = response["output"]
        st.session_state.messages.append({"role": "assistant", "content": output})
        msgs.add_ai_message(output)
        st.write(output)

# === HÀM CHÍNH ===
def render():
    """
    Hàm chính điều khiển luồng chương trình
    """
    initialize_app()
    prompt = st.chat_input("Hãy hỏi tôi đi")
    tab2, tab3 = st.tabs(["Chat", "Lịch sử chat"])
        
    with tab2:
        # Thiết lập sidebar
        setup_sidebar()
        msgs = setup_chat_interface()

        
        agent_executor = agentV1()

        if prompt:      
            handle_user_input(prompt, msgs, agent_executor)

    with tab3:
        # Hiển thị lịch sử trò chuyện
        show_chat_histories()

# Chạy ứng dụng
if __name__ == "__main__":
    render()