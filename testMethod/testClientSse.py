
import httpx
from fastmcp import Client, FastMCP

# apiBaseUrl = "http://localhost:3000/kingworks/sse"
apiBaseUrl = "http://localhost:3000/petstore/sse"
client = httpx.AsyncClient(base_url=apiBaseUrl)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    async with Client(apiBaseUrl) as client:
        tools = await client.list_tools()
        logger.info("Available tools: %s", tools)
        logger.info("Length of tools: %d", len(tools))
        logger.info("Type of tools: %s", type(tools))
        logger.info("string: %s", str(tools[0]))
        for tool in tools:
            logger.info("Tool: %s", tool.name)
        logger.info("First tool name: %s", tools[0].name)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
        