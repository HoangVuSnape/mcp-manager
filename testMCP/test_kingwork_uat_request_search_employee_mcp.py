import requests
from fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()
import os
# Initialize your MCP server
mcp = FastMCP("EmployeeSearchMCP")

# Define your search tool
@mcp.tool(name="search_employee", description="Search employee by name in KingWork API")
def search_employee(name: str) -> dict:
    """
    Search for employee with the given name using KingWork API.
    """
    url = "https://api-uat.kingwork.vn/api/employee/search-employee"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": os.getenv("authorization"),  # Replace securely
        "content-type": "application/json",
        "lang": "en",
        "x-tenant-id": "uat"
    }

    payload = {
        "sort": [{"employeeId": "DESC"}],
        "search": {"name": name},  # Replace here with input param
        "filter": {
            "projectPrimaryName": [],
            "positionName": [],
            "status": ["approved"]
        },
        "limit": 10,
        "offset": 1,
        "fromDate": "2025-05-26",
        "toDate": "2025-06-25",
        "viewType": "all",
        "isAdmin": True
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


mcp.run(transport="sse", port=8000)  # Run the MCP server
