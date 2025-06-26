import requests
from fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()
import os
from utils import remove_vietnamese_tones

# Initialize your MCP server
mcp = FastMCP("ListEmployeeMCP")

# Define your search tool

@mcp.tool(name="list of employee", description="List all employees in KingWork API")
def list_employees() -> dict:
    """
    List all employees using KingWork API.
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
        "search": {"name": ""},  # Replace here with input param
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
    
mcp.run(transport="sse", port=8001) 