# Đây là nơi test các ví dụ của tool
import httpx
from fastmcp import Client
import json
# apiBaseUrl = "http://localhost:3000/kingworks/sse"
apiBaseUrl = "http://localhost:3000/itv/sse"
client = httpx.AsyncClient(base_url=apiBaseUrl)

async def main():
    async with Client(apiBaseUrl) as client:
        tools = await client.list_tools()
        print("Available tools:", tools)
        
        for tool in tools:
            print(f"Tool: {tool.name}")
        
        

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
        