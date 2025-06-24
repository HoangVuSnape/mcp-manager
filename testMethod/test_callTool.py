
import httpx
from fastmcp import Client
import json
# apiBaseUrl = "http://localhost:3000/kingworks/sse"
apiBaseUrl = "http://localhost:3000/petstore/sse"
client = httpx.AsyncClient(base_url=apiBaseUrl)

async def main():
    async with Client(apiBaseUrl) as client:
        tools = await client.list_tools()
        print("Available tools:", tools)
        
        for tool in tools:
            print(f"Tool: {tool.name}")
        # print(tools[0])
        # Tham số truy vấn (tìm thú cưng theo trạng thái)
        params = {
            "status": ["available", "pending"]  # Có thể dùng ["sold"] hoặc bất kỳ kết hợp nào
        }
        
        result = await client.call_tool("findPetsByStatus", arguments=params)
        # print("Result from tool call:", result) 
        # pets = result.json()
        print("length of result:", len(result))
        # print("Result from tool call:", result)
        json_string = result[0].text

        #  Chuyển chuỗi JSON thành danh sách Python
        pets = json.loads(json_string)

        # Duyệt và in từng `id` và `name`
        for pet in pets[:5]:
            pet_id = pet.get('id')
            pet_name = pet.get('name')
            print(f"ID: {pet_id}, Name: {pet_name}")
            print(f"ID: {type(pet_id)}, Name: {type(pet_name)}")
        

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
        