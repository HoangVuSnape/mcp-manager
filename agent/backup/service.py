import asyncio
import os
import shutil
import subprocess
import time
from typing import Any

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings
from dotenv import load_dotenv
load_dotenv()




prompt = """
Bạn là một trợ lý AI, có thể trả lời các câu hỏi và thực hiện các tác vụ theo yêu cầu của người dùng.

Khi bỏ tên vào tool, hãy:
- Xóa dấu tiếng Việt.
- Viết thường chữ cái đầu tiên của mỗi từ.
  Ví dụ: "Đại" → "dai".

Nếu câu hỏi có liên quan đến bảng chấm công, trước hết phải thực hiện:
1) Lấy được ID của nhân viên từ câu hỏi thông qua tool `get_list_employee`.
2) Gọi tool `get_employee_timesheet_month` với ID của nhân viên và tháng/năm cần lấy.

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
    # print(f"\n\nRunning: {question}")
    result = await Runner.run(starting_agent=agent, input=message)
    # print(result.final_output)
    
    return result.final_output

# === Global token cache ===
ACCESS_TOKEN = None

import requests
def get_access_token():
    global ACCESS_TOKEN
    if ACCESS_TOKEN:
        return ACCESS_TOKEN  # Return cached token

    url = "https://api-uat.kingwork.vn/api/auth/signin"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "content-type": "application/json",
        "lang": "en",
        "x-tenant-id": "uat"
    }
    payload = {
        "username": "admin",
        "password": "Aa@123456"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        ACCESS_TOKEN = f'Bearer {data.get("accessToken")}'
        return ACCESS_TOKEN
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

async def main(question):
    # Perform login first to get and cache the JWT token
    token = get_access_token()
    # save it txt token
    with open("token.txt", "w") as f:
        f.write(token)
    if token:
        print("✅ Login successful. JWT token acquired.")
    else:
        print("❌ Login failed. Exiting.")
        return

    async with MCPServerSse(
        name="SSE Python Server",
        params={
            "url": "http://localhost:8000/sse"
        },
        client_session_timeout_seconds=30
    ) as server:
        result = await run(question, server)
        
    return result

if __name__ == "__main__":
    question = "Lấy thôn tin nhân viên có tên là 'đại' từ KingWork API."
    
    print("+++++=+++++")
    result = asyncio.run(main(question))
    print(result)