
import httpx
from fastmcp import Client
import json
import retrievalMCP.models
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


apiBaseUrl = "http://localhost:3000/petstore/sse"
client = httpx.AsyncClient(base_url=apiBaseUrl)
InfoTool = retrievalMCP.models.InfoTool
async def listTool():
    async with Client(apiBaseUrl) as client:
        tools = await client.list_tools()
        # logger.info("Available tools: %s", tools)
        # logger.info("Length of tools: %d", len(tools))
        # logger.info("Type of tools: %s", type(tools))
        # logger.info("string: %s", str(tools[0]))

        result = []
        for tool in tools:
            # logger.info("Tool: %s", tool.name)
            toolvvv = str(tool)
            result.append(InfoTool(tool=toolvvv))
    return result

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(listTool())
    logger.info("Result: %s", result)
    for item in result:
        logger.info("Item: %s", item)
