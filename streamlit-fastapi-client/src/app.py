import streamlit as st
import requests
from utils import fetch_list_servers, fetch_list_tools
# save cache streamlit
# @st.cache_data
from math import ceil
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Custom CSS
st.markdown("""
<style>
    .status-online {
        background-color: #d4edda;
        color: #155724;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-offline {
        background-color: #f8d7da;
        color: #721c24;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-starting {
        background-color: #cce5ff;
        color: #0056b3;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-unknown {
        background-color: #e2e3e5;
        color: #6c757d;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .server-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin: 20px 0;
    }
    .stToggle > div {
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)
st.set_page_config(page_title="MCP Server Management Dashboard", layout="wide")

st.title("🖥️ MCP Server Management Dashboard")
st.caption("Manage and monitor your Model Context Protocol (MCP) servers")


def visualize_servers(list_servers, search_query):
    """Visualize the list of servers."""
    if not list_servers:
        st.write("Không có server nào được tìm thấy.")
        return
    
    st.write("Danh sách các server:")
    # for server in servers:
    #     st.write(f"- {server}")
    
    
    if search_query:
        list_servers = [s for s in list_servers if search_query.lower() in s.lower()]
    else:
        list_servers = [s for s in list_servers if s]  # Filter out empty
    
    print("Filtered servers:", list_servers)
    # Filtered servers: ['petstore', 'kingworks']
    if not list_servers:
        st.write("Không có server nào khớp với tìm kiếm.")
        return
    
        # --- Hiển thị các tool theo dạng 3 cột mỗi dòng ---
    cols_per_row = 4
    num_rows = ceil(len(list_servers) / cols_per_row)

    for row in range(num_rows):
        cols = st.columns(cols_per_row)

        for i in range(cols_per_row):
            index = row * cols_per_row + i
            if index >= len(list_servers):
                break

            server = list_servers[index]
            # print("Server:", server)
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f"##### {server}")
                    st.toggle("Enable", key=f"toggle_{server}", value=True)



def visualize_tools(tools_list, search_query):
    """Visualize the list of tools."""
    if not tools_list:
        st.write("Không có tools nào được tìm thấy.")
        return
    
    st.write("Danh sách các tools:")
    
    # for tool in tools_list:
    #     name = tool.get("name")
    #     enabled = tool.get("enabled")
    #     # st.write(f"Tool: {name} | Enabled: {enabled}")
    
    if search_query:
        tools_list_filtered = [t for t in tools_list if search_query.lower() in t.get("name", "").lower()]
    else:
        tools_list_filtered = [t for t in tools_list if t]
        
    cols_per_row = 4
    num_rows = ceil(len(tools_list_filtered) / cols_per_row)

    for row in range(num_rows):
        cols = st.columns(cols_per_row)

        for i in range(cols_per_row):
            index = row * cols_per_row + i
            if index >= len(tools_list_filtered):
                break

            tool = tools_list_filtered[index]
            name = tool.get("name")
            enabled = tool.get("enabled")
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f"##### {name}")
                    st.toggle("Enable", key=f"toggle_{name}", value=enabled)
    
    # with col4:
    #             # Toggle switch for server state
    #             current_state = server.state == "on"
    #             new_state = st.toggle(
    #                 "Enable", 
    #                 key=f"toggle_{server.id}_{idx}", 
    #                 value=current_state,
    #                 help=f"Toggle {server.name} on/off"
    #             )
                
    #             # Update state if changed
    #             if new_state != current_state:
    #                 state_value = "on" if new_state else "off"
    #                 if mcp_service.toggle_server_state(server.id, state_value):
    #                     st.success(f"✅ {server.name} {'enabled' if new_state else 'disabled'}")
    #                     time.sleep(1)
    #                     st.rerun()
    #                 else:
    #                     st.error(f"❌ Failed to update {server.name}")
    #         st.divider()       


def main():
    st.title("List Servers từ FastAPI")

    host = "http://localhost:3000/"
    list_servers_endpoint = "list-server"
    api_url_server = f"{host}{list_servers_endpoint}"
    
    api_tools_endpoint = "list-tools-enabled"
    api_url_tools = f"{host}{api_tools_endpoint}"
    
    # --- Thanh công cụ ---
    col1, col2, col3, col4, col5 = st.columns([1, 6, 1, 1, 1])

    with col1:
        select_all = st.checkbox("Chọn tất cả", key="select_all_checkbox")

    with col2:
        search_query = st.text_input("Search Tools", placeholder="Enter tool name...")

    with col3:
        st.button("🔍 Search")

    with col4:
        st.button("🔽 Filter")

    
    server, tools = st.tabs(["Server", "Tools"])

    
    with server:
        st.header("Danh sách Server")
        
    
        data = fetch_list_servers(api_url_server)
        list_servers = data.get("servers", [])
        # visualize_servers(list_servers, search_query=search_query)
        
        
        # print("Data type:", type(data))
        # print("Data content:", data["servers"])
        # list_servers = data.get("servers", [])
        # print("List servers:", list_servers)
        # st.write(data)
    with tools:
        st.header("Danh sách Tools")
        
        data = fetch_list_tools(api_url_tools)

        tools_list = data.get("tools", [])
        print("Tools list:", tools_list)
        # create uuid for each tool

        visualize_tools(tools_list, search_query=search_query)


if __name__ == "__main__":
    main()