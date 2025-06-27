import requests
from fastmcp import FastMCP
import os
from utils import remove_vietnamese_tones

# Initialize MCP server
mcp = FastMCP("EmployeeSearchMCP")

# === Global token cache ===
ACCESS_TOKEN = None

def get_access_token():
    global ACCESS_TOKEN
    if ACCESS_TOKEN:
        return ACCESS_TOKEN  # Return cached token

    url = "https://api-uat.kingwork.vn/api/auth/signin"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "content-type": "application/json",
        "lang": "en",
        "x-tenant-id": "uat"
    }
    payload = {
        "username": "admin",
        "password": "Aa@123456"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        ACCESS_TOKEN = f'Bearer {data.get("accessToken")}'
        return ACCESS_TOKEN
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

# ============================ TOOLS ============================

@mcp.tool(name="search_employee", description="Search employee by name in KingWork API")
def search_employee(name: str) -> dict:
    url = "https://api-uat.kingwork.vn/api/employee/search-employee"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": get_access_token(),
        "content-type": "application/json",
        "lang": "en",
        "x-tenant-id": "uat"
    }
    name = remove_vietnamese_tones(name)
    payload = {
        "sort": [{"employeeId": "DESC"}],
        "search": {"name": name},
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

@mcp.tool(name="get_config_leave_off", description="Lấy danh sách loại phép đang hoạt động từ hệ thống KingWork")
def get_config_leave_off() -> dict:
    url = "https://api-uat.kingwork.vn/api/configurations/get-active-config-leave-off"
    headers = {
        "accept": "application/json",
        "x-tenant-id": "uat",
        "Authorization": get_access_token()
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return {"status": "success", "data": response.json()}
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}

@mcp.tool(name="get_leave_detail_by_user", description="Lấy chi tiết loại phép của nhân viên theo userId và năm")
def get_leave_detail_by_user(userId: str, year: str) -> dict:
    url = f"https://api-uat.kingwork.vn/api/timesheet/leave-type-off-employee-detail/{userId}"
    headers = {
        "accept": "*/*",
        "x-tenant-id": "uat",
        "Authorization": get_access_token()
    }
    params = {"year": year}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return {"status": "success", "data": response.json()}
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}

@mcp.tool(name="get_employee_timesheet_month", description="Lấy bảng chấm công theo tháng cho nhân viên cụ thể")
def get_employee_timesheet_month(
    monthYear: str = "2025-04",
    currentDay: str = "0",
    userId: str = "1081e472-dd25-4871-af0a-80c886698781"
) -> dict:
    url = "https://api-uat.kingwork.vn/api/timesheet/working-month/employee-timesheet-month"
    headers = {
        "accept": "application/json",
        "x-tenant-id": "uat",
        "Authorization": get_access_token()
    }
    params = {
        "monthYear": monthYear,
        "currentDay": currentDay,
        "userId": userId
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return {"success": True, "data": response.json()}
    else:
        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text
        }

@mcp.tool(name="list_employees", description="Trả về danh sách nhân viên đã được duyệt, gồm id, firstName và lastName.")
def list_employees():
    url = "https://api-uat.kingwork.vn/api/employee/search-employee"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": get_access_token(),
        "authorizationms": "",
        "content-type": "application/json",
        "lang": "en",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-tenant-id": "uat"
    }
    payload = {
        "sort": [{"employeeId": "DESC"}],
        "search": {"name": ""},
        "filter": {
            "projectPrimaryName": [],
            "positionName": [],
            "status": ["approved"]
        },
        "fromDate": "2025-05-26",
        "toDate": "2025-06-25",
        "viewType": "all",
        "isAdmin": True
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        return {"error": f"Lỗi API: {response.status_code}", "details": response.text}

    data = response.json().get("data", {})
    result_list = data.get("result", [])

    return [
        {
            "id": emp.get("id"),
            "firstName": emp.get("firstName"),
            "lastName": emp.get("lastName")
        }
        for emp in result_list
    ]

@mcp.tool(name="list_leave_off_requests", description="Liệt kê các đơn nghỉ phép đã được duyệt của nhân viên dưới quyền theo thời gian")
def list_leave_off_requests() -> list[dict]:
    url = "https://api-uat.kingwork.vn/api/timesheet/list-mamager-leave-off-employee"
    params = {
        "leaveTypeId": 8,
        "configTypeId": 3,
        "status": "true",
        "fromDate": "2025-06-01",
        "toDate": "2025-06-30"
    }
    headers = {
        "accept": "*/*",
        "x-tenant-id": "uat",
        "authorization": get_access_token()
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        raise Exception(f"Lỗi API {response.status_code}: {response.text}")

@mcp.tool(name="count_projects", description="Lấy tổng số dự án trong hệ thống")
def count_projects() -> int:
    url = "https://api-uat.kingwork.vn/api/project"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": get_access_token(),
        "lang": "en",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-tenant-id": "uat",
        "referer": "https://uat.kingwork.vn/"
    }

    response = requests.get(url, headers=headers)

    if response.ok:
        return response.json().get("data", {}).get("total", 0)
    else:
        raise Exception(f"❌ Lỗi {response.status_code}: {response.text}")

# ============================ ENTRY ============================

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000)
