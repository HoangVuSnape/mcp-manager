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
# load_dotenv()

async def run(mcp_server: MCPServer):
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to answer the questions.",
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),
    )

    # Use the `add` tool to add two numbers
    message = "how many tools we have?"
    # message = "Lấy ra 5 tool có sẵn trong hệ thống và mô tả ngắn gọn về chúng?"
    print(f"Running: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)

    print("=====================================")
    # message = "Gọi đến tool getUserByName và tự truyền tham số và lấy ra kết quả? Không có tự bịa ra kết quả. Nếu gọi tool không có thì sẽ nói không gọi được"
    # # message = "Cách truyền tham số vào tool getUserByName sẵn có?"
    # print(f"\n\nRunning: {message}")
    # result = await Runner.run(starting_agent=agent, input=message)
    # print(result.final_output)

async def main():
    async with MCPServerSse(
        name="SSE Python Server",
        params={
            "url": "http://localhost:3000/itv/sse",
        },
    ) as server:
        await run(server)
        
if __name__ == "__main__":
    asyncio.run(main())