import requests
from fastmcp import FastMCP


# Initialize MCP server
mcp = FastMCP("ITV Assistant")


def load_bearer():
    # read file token.txt

    try:    
        print("Loading token from file...")
        with open("../token.txt", "r") as f:
            bearer = f.read().strip()
        return bearer
    except FileNotFoundError:
        print("Token file not found. Please login first.")
        bearer = None

# ============================ TOOLS ============================
# 1. Thông tin cá nhân
@mcp.tool(name="search_employee", description="Search employee by name in KingWork API")
def search_employee(name: str) -> dict:
    url = "https://api-uat.kingwork.vn/api/employee/search-employee"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": load_bearer(),
        "content-type": "application/json",
        "lang": "en",
        "x-tenant-id": "uat"
    }
    # name = remove_vietnamese_tones(name)
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


# 4. Phép năm & Ngày nghỉ/OT (Leave & Overtime)
@mcp.tool(name="get_config_leave_off", description="Lấy danh sách loại phép")
def get_config_leave_off() -> dict:
    url = "https://api-uat.kingwork.vn/api/configurations/get-active-config-leave-off"
    headers = {
        "accept": "application/json",
        "x-tenant-id": "uat",
        "Authorization": load_bearer()
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    
        leave_names = []
        response = response.json()
        # Truy cập danh sách các năm trong response
        for year in response["data"]:
            leave_types = year.get("leaveTypes", [])
            for leave in leave_types:
                name = leave.get("name")
                id = leave.get("id")
                leave_names.append({"id": id, "name": name})
            
        return {"status": "success", "data": leave_names}
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}


@mcp.tool(name="get_leave_detail_by_user", description="Lấy chi tiết loại phép của nhân viên theo userId và năm")
def get_leave_detail_by_user(userId: str, year: str) -> dict:
    url = f"https://api-uat.kingwork.vn/api/timesheet/leave-type-off-employee-detail/{userId}"
    headers = {
        "accept": "*/*",
        "x-tenant-id": "uat",
        "Authorization": load_bearer()
    }
    params = {"year": year}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return {"status": "success", "data": response.json()}
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}

@mcp.tool(name="get_list_employee", description="Lấy danh sách nhân viên")
def get_list_employee() -> dict:
    url = "https://api-uat.kingwork.vn/api/employee/search-employee"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": load_bearer(),
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

    response = requests.post(url, headers=headers, json=payload, timeout=30)


    # Parse and extract result
    data = response.json().get("data", {})
    result_list = data.get("result", [])
    return [
        {
            "id": emp.get("id"),
            # "firstName": emp.get("firstName"),
            # "lastName": emp.get("lastName")
            "name": f"{emp.get('firstName', '')} {emp.get('lastName', '')}".strip(),
        }
        for emp in result_list
    ]


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
        "Authorization": load_bearer()
    }
    params = {
        "monthYear": monthYear,
        "currentDay": currentDay,
        "userId": userId
    }

    response = requests.get(url, headers=headers, params=params, timeout=30)

    if response.status_code == 200:
        return {"success": True, "data": response.json()}
    else:
        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text
        }



@mcp.tool(name="get_user_leave_info", description="Trả về thông tin ngày phép còn lại trong năm của nhân viên theo userId.")
def get_user_leave_annual(user_id: str):
    """
    Trả về dict gồm: userId, fullName, availableDays
    """

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
        "authorization": load_bearer()  # Lưu token trong .env
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        return {
            "error": f"Lỗi {response.status_code}",
            "message": response.text
        }

    data = response.json()
    employees = data.get("data", [])

    for emp in employees:
        if emp.get("userId") == user_id:
            return {
                "userId": emp.get("userId"),
                "fullName": emp.get("fullName"),
                "availableDays": emp.get("availableDays")
            }

    return {
        "message": f"Không tìm thấy userId: {user_id}"
    }

@mcp.tool(name="count_matching_leave_records_month", description="Trả về thông tin nghỉ phép theo tháng của nhân viên theo userId")
def count_matching_leave_records(user_id: str) -> int:
    url = "https://api-uat.kingwork.vn/api/timesheet/list-mamager-leave-off-employee"
    params = {
        "leaveTypeId": 9,
        "configTypeId": 3,
        "status": "true",
        "fromDate": "2025-06-01",
        "toDate": "2025-06-30"
    }


    headers = {
        "accept": "*/*",
        "x-tenant-id": "uat",
        "authorization": load_bearer()
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print(f"Request failed: {response.status_code}")
        return 0

    data = response.json()
    result = 0

    if "data" in data and isinstance(data["data"], list):
        for item in data["data"]:
            if item.get("userId") == user_id:
                result += 1

    return result

# 6. Dự án (Project Assignment)
@mcp.tool(name="list_projects", description="Lấy tổng số dự án trong hệ thống")
def list_projects():
    url = "https://api-uat.kingwork.vn/api/project"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": load_bearer(),
        "lang": "en",
        "priority": "u=1, i",
        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-tenant-id": "uat",
        "referer": "https://uat.kingwork.vn/"
    }

    response = requests.get(url, headers=headers)

    if not response.ok:
        print(f"❌ Lỗi {response.status_code}: {response.text}")
        return []

    data = response.json()
    projects = data.get("data", {}).get("result", [])
    total_projects = data.get("data", {}).get("total", 0)
    summary_list = [
        {
            "projectCode": proj.get("projectCode"),
            "name": proj.get("name"),
            "description": proj.get("description")
        }
        for proj in projects
    ]

    return summary_list, total_projects

@mcp.tool(name="get_project_duration", description="Lấy thời gian bắt đầu và kết thúc của dự án theo mã dự án")
def get_project_duration(project_name: str):
    """
    Truyền vào tên dự án (hoặc một phần tên), trả về thông tin dự án khớp:
    name, startDate, endDate.
    """
    url = "https://api-uat.kingwork.vn/api/project"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": load_bearer(),
        "lang": "en",
        "priority": "u=1, i",
        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-tenant-id": "uat",
        "referer": "https://uat.kingwork.vn/"
    }

    response = requests.get(url, headers=headers)

    if not response.ok:
        print(f"Lỗi {response.status_code}: {response.text}")
        return None

    data = response.json()
    projects = data.get("data", {}).get("result", [])

    for proj in projects:
        name = proj.get("name", "")
        # So sánh không phân biệt hoa thường và cho phép khớp một phần tên
        if project_name.lower() in name.lower():
            return {
                "name": name,
                "description": proj.get("description"),
                "projectCode": proj.get("projectCode"),
                "startDate": proj.get("startDate"),
                "endDate": proj.get("endDate")
            }

    print(f"Không tìm thấy dự án nào khớp với '{project_name}'")
    return None

@mcp.tool(name="get_project_user_joined", description="Lấy danh sách của dự án mà nhân viên đã tham gia")
def get_project_user_joined(user_id: str):
    """
    Truyền vào userId, trả về projectCode nếu tìm thấy userId trong response,
    ngược lại trả về None.
    """
    url = "https://api-uat.kingwork.vn/api/project-detail/history"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": load_bearer(),
        "lang": "en",
        "priority": "u=1, i",
        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-tenant-id": "uat",
        "referer": "https://uat.kingwork.vn/"
    }

    response = requests.get(url, headers=headers, timeout=60)

    if not response.ok:
        print(f"❌ Lỗi {response.status_code}: {response.text}")
        return None

    data = response.json()
    history_records = data.get("data", {}).get("result", [])
    list_project_joined = []
    for record in history_records:
        if record.get("userId") == user_id:
            list_project_joined.append(record.get("projectCode"))
            
            
    return list_project_joined if list_project_joined else None

# 7. Timesheet & Giờ làm việc (Timesheet & Working Hours) 
@mcp.tool(name="get_time_hours_user", description="Lấy tổng số giờ và ngày làm việc của nhân viên trong tháng")
def get_time_hours_user(userId: str, monthYear: str = "2025-04") -> dict:
    """
    Truyền vào userId và monthYear (yyyy-mm),
    trả về tổng số giờ làm (actualyHoursWorkDays) và số ngày làm (actualyWorkDays)
    nếu lấy dữ liệu thành công, ngược lại trả về lỗi.
    """
    url = "https://api-uat.kingwork.vn/api/timesheet/working-month/employee-timesheet-month"
    headers = {
        "accept": "application/json",
        "x-tenant-id": "uat",
        "Authorization": load_bearer()
    }
    params = {
        "monthYear": monthYear,
        "currentDay": "0",  # luôn truyền giá trị mặc định 0
        "userId": userId
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
    except requests.RequestException as e:
        return {"success": False, "error": f"Lỗi request: {e}"}

    if response.status_code != 200:
        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text
        }

    data = response.json().get("data", {})
    workshifts = data.get("workshifts", [])

    if not workshifts or not workshifts[0].get("workshift"):
        return {"success": False, "error": "Không tìm thấy dữ liệu workshift cho nhân viên."}

    workshift_data = workshifts[0]["workshift"][0]
    actual_hours = workshift_data.get("actualyHoursWorkDays", 0)
    actual_days = workshift_data.get("actualyWorkDays", 0)

    return {
        "success": True,
        "actualyHoursWorkDays": actual_hours,
        "actualyWorkDays": actual_days
    }


@mcp.tool(name="sum_user_not_confirm_timesheet", description="Tính tổng số nhân viên chưa xác nhận của time sheet nhân viên trong tháng")
def sum_user_not_confirm_timesheet(userId: str, monthYear: str = "2025-04") -> dict:
    """
    Truyền vào userId và monthYear (yyyy-mm),
    trả về tổng số nhân viên chưa xác nhận (unconfirmedWorkDays) của time sheet nhân viên trong tháng.
    và trả về tổng số kết quả (total) nếu lấy dữ liệu thành công
    """

    url = "https://api-uat.kingwork.vn/api/timesheet/working-month/get-list-timesheet-working-month"
    params = {
        "isSelectAsLine": "false",
        "limit": "10",
        "monthYear": monthYear,
        "offset": "1",
        "status": "view"
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": load_bearer(),  # Replace with your real token
        "lang": "en",
        "priority": "u=1, i",
        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-tenant-id": "uat",
        "referer": "https://uat.kingwork.vn/"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an error for bad responses
    data = response.json()

    result = 0
    for da in data.get("data", {}).get("result", []):
        # print(da.get("userId"), da.get("fullName"), da.get("actualyWorkDays"), da.get("actualyHoursWorkDays"))
        if da.get("status") == "waiting for confirm":
            result +=1

    return {"success": True, "unconfirmedWorkDays": result, "total": data.get("data", {}).get("totalResult", 0)}


@mcp.tool(name="get_employee_performance_review", description="Lấy đánh giá hiệu suất của nhân viên theo userId")
def get_performance_employees_reviews(search_text=""):
    url = "https://api-uat.kingwork.vn/api/performance/review"
    params = {
        "searchName": search_text
    }
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "authorization": load_bearer(),  # <-- đảm bảo bạn đã set biến token trước
        "lang": "en",
        "x-tenant-id": "uat"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        print("✅ API call successful!")

        # Parse dữ liệu để lấy name và userIds
        if data and data.get("data") and data["data"].get("result"):
            reviews = data["data"]["result"]
            extracted = []
            for review in reviews:
                name = review.get("name", "N/A")
                user_ids = review.get("userIds", [])
                extracted.append({"name": name, "userIds": user_ids})



            return extracted
        else:
            print("❌ Không tìm thấy dữ liệu review phù hợp.")
            return []
    except requests.RequestException as e:
        print(f"❌ API call failed: {e}")
        return []


if __name__ == "__main__":
    mcp.run(transport="sse", port=8000)



