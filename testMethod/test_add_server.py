import httpx

def main():
    url = "http://localhost:3000/add-server"
    payload = {
        "path": "https://petstore3.swagger.io/api/v3/openapi.json",
        "apiBaseUrl": "https://petstore3.swagger.io/api/v3",
        "prefix": "petstore3"
    }
    response = httpx.post(url, json=payload)
    print("Status code:", response.status_code)
    print("Response:", response.json())

if __name__ == "__main__":
    main()