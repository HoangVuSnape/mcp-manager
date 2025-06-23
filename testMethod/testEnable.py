import httpx

url = "http://localhost:3000/tool-enabled"
payload = {
    "prefix": "petstore",
    "name": "petstore_findPetsByStatus",
    "enabled": True
}

response = httpx.post(url, json=payload)
print("Status code:", response.status_code)
print("Response:", response.json())