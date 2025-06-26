from mcp import ClientSession
from mcp.client.sse import sse_client



async def search_employee(name: str):
    async with sse_client("http://127.0.0.1:8000/sse") as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            # List avail tool
            tools = await session.list_tools()
            print(tools)
            print("----------")
            
            result = await session.call_tool("search_employee", arguments={"name": name})
            print(result)
            
            
            
if __name__ == "__main__":
    import asyncio
    # asyncio.run(search_employee(name="dai"))
    asyncio.run(search_employee(name=""))