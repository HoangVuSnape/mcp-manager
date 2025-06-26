import requests
from dotenv import load_dotenv
load_dotenv()
import os
url = "https://api-uat.kingwork.vn/api/employee/search-employee"

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "vi-VN",
    "authorization": os.getenv("authorization"),
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
    "search": {"name": "dai"},
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

response = requests.post(url, headers=headers, json=payload)

print(response.status_code)
print(response.json())
