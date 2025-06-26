import httpx

# url = "http://localhost:3000/tool-enabled"
# payload = {
#     "prefix": "petstore",
#     "name": "petstore_findPetsByStatus",
#     "enabled": True
# }

url = "http://localhost:3000/tool-enabled"
payload = {
    "prefix": "itv",
    "name": "itv_ApplicationController_synchronizedMaster",
    "enabled": True
}

response = httpx.post(url, json=payload)
print("Status code:", response.status_code)
print("Response:", response.json())