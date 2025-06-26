
import httpx

def main():
    url_list_tools_enabled = "http://localhost:3000/list-tools-enabled"
    response = httpx.get(url_list_tools_enabled)
    print("Status code:", response.status_code)
    response_data = response.json()

    print("Number of tools:", len(response_data['tools']))
    # count tool enabled True or False
    count_enabled_true = sum(1 for tool in response_data['tools'] if tool['enabled'])
    count_enabled_false = sum(1 for tool in response_data['tools'] if not tool['enabled'])
    print("Number of tools enabled True:", count_enabled_true)
    print("Number of tools enabled False:", count_enabled_false)
if __name__ == "__main__":
    main()