
import httpx
import tqdm
def main():
    url_list_tools_enabled = "http://localhost:3000/list-tools-enabled"
    response = httpx.get(url_list_tools_enabled)
    print("Status code:", response.status_code)
    # print("Response:", response.json())
    response_data = response.json()
    # print("Response data:", response_data)
    print("Number of tools:", len(response_data['tools']))
    for tool in tqdm.tqdm(response_data['tools']):

        if tool['enabled'] == True:
            url_tool_enabled = "http://localhost:3000/tool-enabled"
            payload = {
                "prefix": "itv",
                "name": tool['name'],
                "enabled": False
            }

            response = httpx.post(url_tool_enabled, json=payload)
            print("Status code:", response.status_code)

if __name__ == "__main__":
    main()