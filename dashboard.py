import gradio as gr
import httpx

API_URL = "http://localhost:3000"
client = httpx.Client()

def list_servers() -> list[str]:
    try:
        resp = client.get(f"{API_URL}/list-server")
        resp.raise_for_status()
        return resp.json().get("servers", [])
    except Exception:
        return []

def list_tools(prefix: str) -> list[str]:
    if not prefix:
        return []
    try:
        resp = client.get(f"{API_URL}/list-tools", params={"prefix": prefix})
        resp.raise_for_status()
        return resp.json().get("tools", [])
    except Exception:
        return []

def add_server(path: str, api_base: str, prefix: str) -> str:
    data = {"path": path, "apiBaseUrl": api_base, "prefix": prefix or None}
    try:
        resp = client.post(f"{API_URL}/add-server", json=data)
        resp.raise_for_status()
        out = resp.json()
        return f"Added {out['added']} with {out['tools']} tools"
    except Exception as exc:
        return f"Error: {exc}"

def set_tool_enabled(prefix: str, tool: str, enabled: bool) -> str:
    data = {"prefix": prefix, "name": tool, "enabled": enabled}
    try:
        resp = client.post(f"{API_URL}/tool-enabled", json=data)
        resp.raise_for_status()
        out = resp.json()
        return f"Tool {out['tool']} enabled: {out['enabled']}"
    except Exception as exc:
        return f"Error: {exc}"

def set_search_enabled(prefix: str, enabled: bool) -> str:
    data = {"prefix": prefix, "enabled": enabled}
    try:
        resp = client.post(f"{API_URL}/search-enabled", json=data)
        resp.raise_for_status()
        out = resp.json()
        return f"Search for {out['prefix']} enabled: {out['enabled']}"
    except Exception as exc:
        return f"Error: {exc}"

def search_tools(prefix: str, name: str, status: str) -> str:
    params = {}
    if prefix:
        params["prefix"] = prefix
    if name:
        params["name"] = name
    if status == "Enabled":
        params["enabled"] = "true"
    elif status == "Disabled":
        params["enabled"] = "false"
    try:
        resp = client.get(f"{API_URL}/search", params=params)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return "No results"
        return "\n".join(f"{r['prefix']}: {r['tool']}" for r in results)
    except Exception as exc:
        return f"Error: {exc}"

with gr.Blocks(title="MCP Server Dashboard") as demo:
    with gr.Tab("Add Server"):
        path_in = gr.Textbox(label="Spec Path or URL")
        api_in = gr.Textbox(label="API Base URL")
        prefix_in = gr.Textbox(label="Prefix")
        add_btn = gr.Button("Add")
        add_out = gr.Textbox(label="Result")
        add_btn.click(add_server, inputs=[path_in, api_in, prefix_in], outputs=add_out)

    with gr.Tab("Tools"):
        server_drop = gr.Dropdown(choices=list_servers(), label="Server")
        refresh_btn = gr.Button("Refresh Servers")
        tool_drop = gr.Dropdown(label="Tool")
        enabled_chk = gr.Checkbox(label="Enabled", value=True)
        set_btn = gr.Button("Set")
        result_box = gr.Textbox(label="Result")

        refresh_btn.click(lambda: gr.update(choices=list_servers()), None, server_drop)
        server_drop.change(lambda p: gr.update(choices=list_tools(p)), server_drop, tool_drop)
        set_btn.click(set_tool_enabled, inputs=[server_drop, tool_drop, enabled_chk], outputs=result_box)

    with gr.Tab("Search Toggle"):
        search_server = gr.Dropdown(choices=list_servers(), label="Server")
        search_chk = gr.Checkbox(label="Search Enabled", value=True)
        search_btn = gr.Button("Set")
        search_out = gr.Textbox(label="Result")
        search_refresh = gr.Button("Refresh Servers")

        search_btn.click(set_search_enabled, inputs=[search_server, search_chk], outputs=search_out)
        search_refresh.click(lambda: gr.update(choices=list_servers()), None, search_server)

    with gr.Tab("Search Tools"):
        filter_server = gr.Dropdown(choices=list_servers(), label="Server")
        name_in = gr.Textbox(label="Name Contains")
        status_drop = gr.Dropdown(choices=["All", "Enabled", "Disabled"], value="All", label="Search Status")
        find_btn = gr.Button("Search")
        result_box2 = gr.Textbox(label="Results")
        search_refresh2 = gr.Button("Refresh Servers")

        find_btn.click(search_tools, inputs=[filter_server, name_in, status_drop], outputs=result_box2)
        search_refresh2.click(lambda: gr.update(choices=list_servers()), None, filter_server)

if __name__ == "__main__":
    demo.launch()
