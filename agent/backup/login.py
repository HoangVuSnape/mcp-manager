import requests
def get_access_token(username, password, x_tenant_id):
    url = "https://api-uat.kingwork.vn/api/auth/signin"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi-VN",
        "content-type": "application/json",
        "lang": "en",
        "x-tenant-id": x_tenant_id
    }
    payload = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        result = f'Bearer {data.get("accessToken")}'
        
        with open("E:\\Innotech\\mcp-manager\\agent\\token.txt", "w") as file:
            file.write(result)
            
        return result
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


if __name__ == "__main__":
    # Replace with your actual username, password, and tenant ID
    username = "admin"
    password = "Aa@123456"
    x_tenant_id = "uat"
    token = get_access_token(username, password, x_tenant_id)

    # write token to file
    with open("E:\\Innotech\\mcp-manager\\agent\\token.txt", "w") as file:
        file.write(token)