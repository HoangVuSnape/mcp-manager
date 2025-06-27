
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import warnings
warnings.filterwarnings("ignore")  # Tắt tất cả cảnh báo
from langchain_openai import ChatOpenAI 
import asyncio
from dotenv import load_dotenv

load_dotenv()
import os
from service import main
from langchain_openai import ChatOpenAI 


llm = ChatOpenAI(
    temperature=0,
    streaming=True,
    model='gpt-4o-mini',
    api_key=os.getenv("OPENAI_API_KEY"))


@tool
def itv_assistant(question):
    """Đầu vào là câu hỏi người dùng Hỗ trợ trả lời hỏi liên quan đến hệ thống KingWork."""
    result = asyncio.run(main(question))
    
    return result

tools = [itv_assistant]

# === 3. Create LLM and AgentExecutor ===
def get_llm_and_agent() -> AgentExecutor:
    """
    Create and return an AgentExecutor using the Vertex AI model and tools.
    """
    system = """
        Bạn là một trợ lý AI kết nối trực tiếp với hệ thống KingWork qua tool `itv_assistant`. 
        Kết quả trả về của tool sẽ được sử dụng để hiển thị cho người dùng.

        - MỌI câu hỏi của người dùng **PHẢI** được gửi vào tool `itv_assistant` để xử lý. 
        Không được trả lời trực tiếp nếu không có sự hỗ trợ của tool.

        Khi người dùng đặt câu hỏi, ví dụ:
        - “Lấy thông tin nhân viên Đại”
        - “Lấy bảng chấm công tháng 05/2025 cho Đại”

        Bạn phải gọi tool như sau:
        itv_assistant("…nguyên văn câu hỏi…")

        Sau khi tool trả kết quả, trả lời người dùng bằng kết quả trả về từ tool.

        Ví dụ hội thoại:

        Người dùng: “Lấy bảng chấm công tháng 5 2025 cho nhân viên Đại.”
        Bạn: itv_assistant("Lấy bảng chấm công tháng 5 2025 cho nhân viên Đại.")
        Trả lời:
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