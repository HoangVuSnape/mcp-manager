
import httpx
from fastmcp import Client
import json
import retrievalMCP.models
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


apiBaseUrl = "http://localhost:3000/petstore/sse"
client = httpx.AsyncClient(base_url=apiBaseUrl)
Pet = retrievalMCP.models.Pet
async def calltool():
    async with Client(apiBaseUrl) as client:
        # tools = await client.list_tools()
        params = {
            "status": ["available", "pending"]  # Có thể dùng ["sold"] hoặc bất kỳ kết hợp nào
        }
        
        result = await client.call_tool("findPetsByStatus", arguments=params)

        json_string = result[0].text

        #  Chuyển chuỗi JSON thành danh sách Python
        pets = json.loads(json_string)

        result10 = []
        # Duyệt và in từng `id` và `name`
        for pet in pets[:10]:
            pet_id = pet.get('id')

            pet_name = pet.get('name')
            result10.append(Pet(id=pet_id, name=pet_name))
        
        logger.info("First 10 pets: %s", result10)
    return result10

if __name__ == "__main__":
    import asyncio
    asyncio.run(calltool())
