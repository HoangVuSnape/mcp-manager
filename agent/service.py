import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings
import requests
from dotenv import load_dotenv
load_dotenv()


prompt = """
Bạn là một trợ lý AI, có thể trả lời các câu hỏi và thực hiện các tác vụ theo yêu cầu của người dùng.

Khi bỏ tên vào tool, hãy:
- Xóa dấu tiếng Việt.
- Viết thường chữ cái đầu tiên của mỗi từ.
  Ví dụ: "Đại" → "dai".

Chú ý:
- Chỉ gọi `get_employee_timesheet_month` khi trong câu hỏi có yêu cầu lấy bảng chấm công (timesheet). Nếu không, hãy sử dụng tool khác phù hợp.
- Khi tool cần tham số `userId`, bắt buộc phải gọi trước tool `get_list_employee` để lấy ID, rồi mới truyền ID vào tool tiếp theo. Hãy hiển thị ID nhân viên tìm được trước khi trả lời kết quả cho người dùng.
- Không được tự bịa kết quả. Nếu không gọi được tool hoặc tool trả về lỗi, cần trả lời rằng không gọi được.
- Ghi lại tất cả các tool đã sử dụng trong quá trình trả lời và in ra cùng kết quả.

"""
async def run(question, mcp_server: MCPServer):
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to answer the questions.",
        model="gpt-4o-mini",
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),
    )
    

    message = f"prompt {prompt} \n Question: {question} \n Trả lời: "
    result = await Runner.run(starting_agent=agent, input=message)

    
    return result.final_output

async def main(question):
    # Perform login first to get and cache the JWT token

    async with MCPServerSse(
        name="SSE Python Server",
        params={
            "url": "http://localhost:8000/sse"
        },
        client_session_timeout_seconds=30
    ) as server:
        result = await run(question, server)
        
    return result

def get_access_token(username, password, x_tenant_id):
    url = "https://api-uat.kingwork.vn/api/auth/signin"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "content-type": "application/json",
        "lang": "en",
        "x-tenant-id": x_tenant_id
    }
    payload = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        result = f'Bearer {data.get("accessToken")}'
        
        with open("./token.txt", "w") as file:
            file.write(result)
            
        return result
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


if __name__ == "__main__":
    question = "Lấy thông tin nhân viên có tên là 'đại' từ KingWork API."
    
    print("+++++=+++++")
    result = asyncio.run(main(question))
    print(result)