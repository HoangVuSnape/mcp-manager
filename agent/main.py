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
    # message = "what tools we have?"
    # print(f"Running: {message}")
    # result = await Runner.run(starting_agent=agent, input=message)
    # print(result.final_output)

    # # Run the `get_weather` tool
    # message = "Summary all tools we have and how many tools we have?"
    # print(f"\n\nRunning: {message}")
    # result = await Runner.run(starting_agent=agent, input=message)
    # print(result.final_output)

    # # Run the `get_secret_word` tool
    # message = "Cách truyền tham số vào tool sẵn có?"
    # print(f"\n\nRunning: {message}")
    # result = await Runner.run(starting_agent=agent, input=message)
    # print(result.final_output)
    
    
    # message = "Gọi đến tool findPetsByStatus và tự truyền tham số và lấy ra kết quả? Không có tự bịa ra kết quả. Nếu gọi tool không có thì sẽ nói không gọi được"
    # print(f"\n\nRunning: {message}")
    # result = await Runner.run(starting_agent=agent, input=message)
    # print(result.final_output)
    ############################### Kingworks SSE ######################################
    # message = "what tools we have?"
    # print(f"Running: {message}")
    # result = await Runner.run(starting_agent=agent, input=message)
    # print(result.final_output)

    print("=====================================")
    # message = "Gọi đến tool getUserByName và tự truyền tham số và lấy ra kết quả? Không có tự bịa ra kết quả. Nếu gọi tool không có thì sẽ nói không gọi được"
    # # message = "Cách truyền tham số vào tool getUserByName sẵn có?"
    # print(f"\n\nRunning: {message}")
    # result = await Runner.run(starting_agent=agent, input=message)
    # print(result.final_output)
    
    message = "Lấy thôn tin nhân viên có tên là 'dai' từ KingWork API. Không có tự bịa ra kết quả. Nếu gọi tool không có thì sẽ nói không gọi được"
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)
    
    
    
# async def main():
#     async with MCPServerSse(
#         name="SSE Python Server",
#         params={
#             "url": "http://localhost:3000/petstore/sse",
#         },
#     ) as server:
#         await run(server)

async def main():
    async with MCPServerSse(
        name="SSE Python Server",
        params={
            "url": "http://localhost:8000/sse",
        },
    ) as server:
        await run(server)
        
if __name__ == "__main__":
    asyncio.run(main())