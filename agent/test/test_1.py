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


prompt = """Bạn là một trợ lý AI, có thể trả lời các câu hỏi và thực hiện các tác vụ theo yêu cầu của người dùng.
Không có tự bịa ra kết quả. Nếu gọi tool không có thì sẽ nói không gọi được.  

Khi bỏ tên vào tool thì xóa dấu  và viết thường chữ đầu tiên của từ đó. 
ví dụ đại -> dai

"""

async def run(mcp_server: MCPServer):
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to answer the questions.",
        model="gpt-4o-mini",
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),
    )

    question = "how many tools we have?"
    print(f"Running: {question}")
    result = await Runner.run(starting_agent=agent, input=question)
    print(result.final_output)

    print("=====================================")
    question = "Lấy thông tin nhân viên có tên là 'đại' từ KingWork API."
    message = f"prompt {prompt} \n Question: {question} \n Trả lời: "
    
    print(f"\n\nRunning: {question}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)
    

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

async def main():
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
            "url": "http://localhost:8000/sse",
        },
        client_session_timeout_seconds=30
    ) as server:
        await run(server)
        
if __name__ == "__main__":
    asyncio.run(main())