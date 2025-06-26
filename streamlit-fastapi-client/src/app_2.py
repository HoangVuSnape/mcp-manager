import streamlit as st
import requests
from utils import fetch_list_servers, fetch_list_tools, tool_enabled
from math import ceil
import logging
import time
import httpx
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

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
    .tool-card {
        padding: 4px;
        margin: 8px 0;

    }
    .tool-name {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 8px;
    }
    .tool-prefix {
        font-size: 12px;
        color: #7f8c8d;
        background-color: #ecf0f1;
        padding: 2px 8px;
        border-radius: 12px;
        display: inline-block;
        margin-bottom: 10px;
    }
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin: 20px 0;
    }
    .stToggle > div {
        margin-top: 10px;
    }
    .search-container {
        background-color: #091017;
        padding: 2px;
        border-radius: 1px;
        margin-bottom: 1px;
    }
    .select-all-checkbox {
        margin-right: 0px; 
        margin-top: 30px;
    }
    .pagination-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 20px 0;
        gap: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="MCP Server Management Dashboard", layout="wide")

st.title("🖥️ MCP Server Management Dashboard")
st.caption("Manage and monitor your Model Context Protocol (MCP) servers")

# Constants for pagination
TOOLS_PER_PAGE = 30
COLS_PER_ROW = 3

def update_all_tools_filtered(tools_list, enable_all, api_url_tools_toggle, search_query="", status_filter="All"):
    """Update all filtered tools to enabled or disabled state"""
    # Apply filters first
    filtered_tools = apply_filters(tools_list, search_query, status_filter)
    
    if not filtered_tools:
        return False, "No tools to update"
    
    success_count = 0
    failed_tools = []
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, tool in enumerate(filtered_tools):
        name = tool.get("name", "")
        enabled = tool.get("enabled", False)
        
        # Only update if state is different
        if enabled != enable_all:
            prefix = name.split("_")[0] if "_" in name else name
            
            payload = {
                "prefix": prefix,
                "name": name,
                "enabled": enable_all
            }
            
            status_text.text(f"Updating {name}...")
            
            try:
                result = tool_enabled(api_url_tools_toggle, payload)
                if result:
                    success_count += 1
                else:
                    failed_tools.append(name)
            except Exception as e:
                failed_tools.append(f"{name} (Error: {str(e)})")
        
        # Update progress
        progress_bar.progress((i + 1) / len(filtered_tools))
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    return success_count > 0, f"Updated {success_count} tools successfully" + (f", Failed: {failed_tools}" if failed_tools else "")

def visualize_servers(select_all, list_servers, search_query):
    """Visualize the list of servers."""
    if not list_servers:
        st.info("📭 Không có server nào được tìm thấy.")
        return
    
    # Filter servers based on search query
    if search_query:
        filtered_servers = [s for s in list_servers if search_query.lower() in s.lower()]
    else:
        filtered_servers = [s for s in list_servers if s]  # Filter out empty
    
    if not filtered_servers:
        st.warning("🔍 Không có server nào khớp với tìm kiếm.")
        return
    
    st.info(f"📊 Tìm thấy {len(filtered_servers)} server(s)")
    
    # Display servers in grid layout
    cols_per_row = 4
    num_rows = ceil(len(filtered_servers) / cols_per_row)

    for row in range(num_rows):
        cols = st.columns(cols_per_row)

        for i in range(cols_per_row):
            index = row * cols_per_row + i
            if index >= len(filtered_servers):
                break

            server = filtered_servers[index]
            with cols[i]:
                with st.container():
                    st.markdown(f"""
                    <div class="server-card">
                        <h4>🖥️ {server}</h4>
                    </div>
                    """, unsafe_allow_html=True)

def apply_filters(tools_list, search_query, status_filter):
    """Apply search and status filters to tools list"""
    if not tools_list:
        return []
    
    filtered_tools = tools_list
    
    # Apply search filter
    if search_query:
        filtered_tools = [t for t in filtered_tools if search_query.lower() in t.get("name", "").lower()]
    
    # Apply status filter
    if status_filter and status_filter != "All":
        if status_filter == "Enabled":
            filtered_tools = [t for t in filtered_tools if t.get("enabled", False)]
        elif status_filter == "Disabled":
            filtered_tools = [t for t in filtered_tools if not t.get("enabled", False)]
        else:
            # Filter by prefix
            filtered_tools = [t for t in filtered_tools if t.get("name", "").startswith(status_filter)]
    
    return filtered_tools

def visualize_tools(filtered_tools, api_url_tools_toggle, current_page=1):
    """Visualize the list of tools with pagination and toggle functionality."""
    if not filtered_tools:
        st.info("📭 Không có tools nào được tìm thấy.")
        return [], False
    
    # Pagination logic
    total_pages = ceil(len(filtered_tools) / TOOLS_PER_PAGE)
    
    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Trước", use_container_width=True, disabled=(current_page <= 1)):
            st.session_state.current_page = max(1, current_page - 1)
            st.rerun()

    with col2:
        st.markdown(f"<h6 style='text-align: center;'>Trang {current_page} / {total_pages}</h6>", unsafe_allow_html=True)

    with col3:
        if st.button("Tiếp ➡️", use_container_width=True, disabled=(current_page >= total_pages)):
            st.session_state.current_page = min(total_pages, current_page + 1)
            st.rerun()
    
    # Get tools for current page
    start_idx = (current_page - 1) * TOOLS_PER_PAGE
    end_idx = start_idx + TOOLS_PER_PAGE
    tools_on_page = filtered_tools[start_idx:end_idx]
    
    st.info(f"🔧 Hiển thị {len(tools_on_page)} / {len(filtered_tools)} tool(s) - Trang {current_page}")
    
    # Initialize session state for individual checkboxes if not exists
    if 'individual_selections' not in st.session_state:
        st.session_state.individual_selections = {}
    
    selected_tools = []
    
    # Get current select_all state
    select_all = st.session_state.get('select_all_checkbox', False)
    
    # Display tools in grid layout
    num_rows = ceil(len(tools_on_page) / COLS_PER_ROW)

    for row in range(num_rows):
        cols = st.columns(COLS_PER_ROW)

        for i in range(COLS_PER_ROW):
            index = row * COLS_PER_ROW + i
            if index >= len(tools_on_page):
                break

            tool = tools_on_page[index]
            name = tool.get("name", "")
            enabled = tool.get("enabled", False)
            
            # Extract prefix from tool name
            prefix = name.split("_")[0] if "_" in name else name
            
            with cols[i]:
                with st.container(border=True):
                    
                    c1, c2 = st.columns([0.2, 5])
                    with c1:
                        # Individual checkbox logic
                        checkbox_key = f"checkbox_{name}"
                        
                        # Initialize individual selection state based on select_all
                        if checkbox_key not in st.session_state.individual_selections:
                            st.session_state.individual_selections[checkbox_key] = select_all
                        
                        # If select_all changed, update this checkbox
                        if select_all:
                            checkbox_value = True
                        else:
                            checkbox_value = st.session_state.individual_selections.get(checkbox_key, False)
                        
                        # Create checkbox
                        individual_selected = st.checkbox(
                            "", 
                            value=checkbox_value, 
                            key=f"checkbox_display_{name}_{current_page}",
                            on_change=lambda name=name: handle_individual_checkbox_change(name)
                        )
                        
                        # Update selection state
                        st.session_state.individual_selections[checkbox_key] = individual_selected
                        
                        # Track selections
                        if individual_selected:
                            selected_tools.append(name)
                    
                    with c2:
                        st.markdown(f"""
                        <div class="tool-card">
                            <div class="tool-prefix">{prefix}</div>
                            <div class="tool-name">{name}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Tool toggle with callback
                        new_state = st.toggle(
                            "Enable Tool", 
                            key=f"tool_toggle_{name}_{current_page}", 
                            value=enabled,
                            help=f"Enable/Disable {name}"
                        )
                    
                    # Handle toggle state change
                    if new_state != enabled:
                        # Prepare payload for API call
                        payload = {
                            "prefix": prefix,
                            "name": name,
                            "enabled": new_state
                        }
                        
                        # Call API to update tool state
                        with st.spinner(f"Updating {name}..."):
                            try:
                                result = tool_enabled(api_url_tools_toggle, payload)
                                if result:
                                    st.success(f"✅ {name} {'enabled' if new_state else 'disabled'}")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to update {name}")
                            except Exception as e:
                                st.error(f"❌ Error updating {name}: {str(e)}")
    
    # Check if any individual checkbox is selected
    any_individual_selected = any(st.session_state.individual_selections.get(f"checkbox_{tool.get('name', '')}", False) 
                                  for tool in filtered_tools)
    
    return selected_tools, any_individual_selected

def handle_individual_checkbox_change(tool_name):
    """Handle individual checkbox state changes"""
    checkbox_key = f"checkbox_{tool_name}"
    current_state = st.session_state.get(f"checkbox_display_{tool_name}_{st.session_state.get('current_page', 1)}", False)
    
    # Update the individual selection state
    st.session_state.individual_selections[checkbox_key] = current_state
    
    # If any individual checkbox is unchecked, uncheck select_all
    if not current_state and st.session_state.get('select_all_checkbox', False):
        st.session_state.select_all_checkbox = False

def sidebar():
    st.sidebar.title("🔧 Add Server Configuration")

    # Nhập URL của server
    url = st.sidebar.text_input("URL", "http://localhost:3000/add-server")

    # Nhập các giá trị payload
    path = st.sidebar.text_input("Path", "https://petstore3.swagger.io/api/v3/openapi.json")
    api_base_url = st.sidebar.text_input("API Base URL", "https://petstore3.swagger.io/api/v3")
    prefix = st.sidebar.text_input("Prefix", "petstore3")

    if st.sidebar.button("➕ Add Server"):
        payload = {
            "path": path,
            "apiBaseUrl": api_base_url,
            "prefix": prefix
        }

        try:
            result = tool_enabled(url, payload)
            if result:
                st.success(f"✅ Added server {prefix} successfully")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error(f"❌ Failed to update")
        except Exception as e:
            st.error(f"❌ Error updating: {str(e)}")

def main():
    # API Configuration
    host = "http://localhost:3000/"
    list_servers_endpoint = "list-server"
    api_url_server = f"{host}{list_servers_endpoint}"
    
    api_tools_endpoint = "list-tools-enabled"
    api_url_tools = f"{host}{api_tools_endpoint}"
    
    # API endpoint for toggling tools
    api_tools_toggle_endpoint = "tool-enabled"  # Adjust this endpoint as needed
    api_url_tools_toggle = f"{host}{api_tools_toggle_endpoint}"
    
    sidebar()
    
    # Initialize session state
    if 'tools_data' not in st.session_state:
        st.session_state.tools_data = []
    if 'individual_selections' not in st.session_state:
        st.session_state.individual_selections = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # Search and Control Panel
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns([1, 4, 1, 1, 1])

    with col1:
        # Handle Select All logic
        st.markdown('<div class="select-all-checkbox">', unsafe_allow_html=True)
        select_all_changed = st.checkbox("🔘 Select All", key="select_all_checkbox")
        
        # When Select All state changes, update all individual checkboxes
        if 'prev_select_all_state' not in st.session_state:
            st.session_state.prev_select_all_state = False
            
        if st.session_state.prev_select_all_state != select_all_changed:
            # Select All state changed
            if select_all_changed:
                # Select all - set all individual checkboxes to True
                for tool in st.session_state.tools_data:
                    name = tool.get("name", "")
                    checkbox_key = f"checkbox_{name}"
                    st.session_state.individual_selections[checkbox_key] = True
            else:
                # Deselect all - set all individual checkboxes to False
                for tool in st.session_state.tools_data:
                    name = tool.get("name", "")
                    checkbox_key = f"checkbox_{name}"
                    st.session_state.individual_selections[checkbox_key] = False
            
            st.session_state.prev_select_all_state = select_all_changed
        
        select_all = select_all_changed

    with col2:
        search_query = st.text_input("", placeholder="Enter server/tool name...")

    with col3:
        # Get unique prefixes for filter options
        all_prefixes = set()
        if 'tools_data' in st.session_state and st.session_state.tools_data:
            for tool in st.session_state.tools_data:
                name = tool.get("name", "")
                prefix = name.split("_")[0] if "_" in name else name
                all_prefixes.add(prefix)
        
        # Create filter options
        filter_options = ["All"]
        filter_options.extend(sorted(all_prefixes))
        filter_options.extend(["Enabled", "Disabled"])
        
        status_filter = st.selectbox(
            "Status",
            options=filter_options,
            help="Filter tools by status or prefix"
        )
        
    with col4:
        st.markdown('<div class="select-all-checkbox">', unsafe_allow_html=True)
        col4a, col4b = st.columns(2)
        with col4a:
            on_all_btn = st.button("🟢All On", help="Enable all")
        with col4b:
            off_all_btn = st.button("🔴All Off", help="Disable all")
    
    with col5:
        st.markdown('<div class="select-all-checkbox">', unsafe_allow_html=True)
        refresh_btn = st.button("🔄 Refresh", help="Refresh data")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Main tabs
    server_tab, tools_tab = st.tabs(["🖥️ Servers", "🔧 Tools"])
    
    with server_tab:
        st.header("📋 Server Management")
        
        try:
            with st.spinner("Loading servers..."):
                data = fetch_list_servers(api_url_server)
                list_servers = data.get("servers", [])
                
            if refresh_btn:
                st.rerun()
                
            visualize_servers(select_all, list_servers, search_query=search_query)
            
        except Exception as e:
            st.error(f"❌ Error loading servers: {str(e)}")
    
    with tools_tab:
        st.header("🔧 Tool Management")
        
        try:
            with st.spinner("Loading tools..."):
                data = fetch_list_tools(api_url_tools)
                tools_list = data.get("tools", [])
                st.session_state.tools_data = tools_list
                
            if refresh_btn:
                # Reset page to 1 when refreshing
                st.session_state.current_page = 1
                st.rerun()
            
            # Apply filters to get filtered tools
            filtered_tools = apply_filters(tools_list, search_query, status_filter)
            
            # Reset to page 1 if current page is beyond available pages
            total_pages = ceil(len(filtered_tools) / TOOLS_PER_PAGE) if filtered_tools else 1
            if st.session_state.current_page > total_pages:
                st.session_state.current_page = 1
            
            # Get tool selection info with pagination
            selected_tools, any_individual_selected = visualize_tools(
                filtered_tools, 
                api_url_tools_toggle, 
                st.session_state.current_page
            )
            
            # Handle All On/Off buttons with improved logic
            if on_all_btn or off_all_btn:
                if not select_all:
                    st.warning("⚠️ Please select 'Select All' checkbox first to enable/disable all tools.")
                else:
                    # All selected via Select All checkbox
                    enable_all = on_all_btn
                    action_text = "Enabling" if enable_all else "Disabling"
                    
                    with st.spinner(f"{action_text} all filtered tools..."):
                        success, message = update_all_tools_filtered(
                            filtered_tools, 
                            enable_all, 
                            api_url_tools_toggle, 
                            search_query,
                            status_filter
                        )
                        if success:
                            st.success(f"✅ {message}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            
        except Exception as e:
            st.error(f"❌ Error loading tools: {str(e)}")

if __name__ == "__main__":
    main()