import datetime
import pytz
from google.oauth2 import service_account
from langchain_google_vertexai import ChatVertexAI
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import warnings
warnings.filterwarnings("ignore")  # Tắt tất cả cảnh báo
from langchain_openai import ChatOpenAI 
import asyncio
from service import search_employee
from dotenv import load_dotenv
load_dotenv()
import os

from utils import remove_vietnamese_tones
# # === 1. Setup Vertex AI with credentials ===
credentials_path = r"E:\Innotech\mcp-manager\credientials\creadientials_vertex.json"
credentials = service_account.Credentials.from_service_account_file(credentials_path)

##########
llm = ChatVertexAI(
    model="gemini-2.0-flash-001",
    streaming= True, 
    temperature=0.5,
    credentials=credentials,
    max_retries=5
)

# llm = ChatOpenAI(
#             temperature=0,
#             streaming=True,
#             model='gpt-4o-mini',
#             api_key=os.getenv("OPENAI_API_KEY"))

# === 2. Define tools ===
@tool
def get_current_time_vietnam() -> str:
    """Lấy thời gian hiện tại của Việt nam (UTC+7)."""
    try:
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        vietnam_time = datetime.datetime.now(vietnam_tz)
        return vietnam_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"Error in retrieving time: {e}"



@tool
def search_employee_ITV(name: str):
    """Lấy thông tin cá nhân của nhân viên theo tên từ KingWork API."""
    name =  remove_vietnamese_tones(name)  # Loại bỏ dấu tiếng Việt
    result = asyncio.run(search_employee(name=name))
    return result

# @tool
# def list_tool() -> list:
#     """Gọi công cụ để thực hiện lấy thông tin các tool có sẵn từ server mcp"""
#     return listTool()
tools = [get_current_time_vietnam, search_employee_ITV]

# === 3. Create LLM and AgentExecutor ===
def get_llm_and_agent() -> AgentExecutor:
    """
    Create and return an AgentExecutor using the Vertex AI model and tools.
    """
    system = """
    Bạn là một trợ lý ảo thông minh, có khả năng trả lời câu hỏi và thực hiện các tác vụ khác nhau.
    Bạn có thể sử dụng các công cụ để lấy thông tin thời gian hiện tại của Việt Nam và tìm kiếm thông tin nhân viên từ KingWork API.
    Hãy trả lời câu hỏi của người dùng một cách chính xác và nhanh chóng.
    Bạn có thể sử dụng các công cụ sau:
    1. `get_current_time_vietnam`: Lấy thời gian hiện tại của Việt Nam (UTC+7).
    2. `search_employee_ITV`: Lấy thông tin cá nhân của nhân viên theo tên từ KingWork API.
    Hãy sử dụng các công cụ này khi cần thiết để cung cấp câu trả lời chính xác và đầy đủ nhất cho người dùng.
    
    Ví dụ:
    - Thông tin cá nhân của bạn đại -> search_employee_ITV("đại")

    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create the agent
    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
    
    # Return the AgentExecutor
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    
    # Initialize the agent executor
    agent_executor = get_llm_and_agent()