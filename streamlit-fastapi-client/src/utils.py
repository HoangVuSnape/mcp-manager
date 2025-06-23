import httpx


def fetch_list_servers(url: str) -> dict:
    """Fetch the list of servers from the given URL."""
    try:
        response = httpx.get(url)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return {}


def fetch_list_tools(url: str) -> dict:
    """Fetch the list of tools from the given URL."""
    try:
        response = httpx.get(url)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return {}

def tool_enabled(url: str, payload: dict) -> dict:
    """Enable or disable a tool using the given URL and payload."""
    try:
        response = httpx.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return {}

