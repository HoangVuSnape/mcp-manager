
import httpx
from fastmcp import Client, FastMCP

apiBaseUrl = "http://localhost:3000/kingworks/sse"
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
        