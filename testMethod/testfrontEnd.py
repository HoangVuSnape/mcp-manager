import streamlit as st
from math import ceil

# Constants
TOOLS_PER_PAGE = 30
COLS_PER_ROW = 3  # Tool cards per row

# 🔧 Tạo dữ liệu mẫu (mock tools)
filtered_tools = [
    {
        "name": f"tool_{i:03}",               # tool_001, tool_002...
        "enabled": i % 2 == 0                 # tool chẵn thì bật
    }
    for i in range(1, 101)  # 100 tools từ 1 đến 100
]

# 🧭 Khởi tạo trạng thái phân trang
total_pages = ceil(len(filtered_tools) / TOOLS_PER_PAGE)
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# 📄 Điều hướng phân trang
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅️ Trước", use_container_width=True) and st.session_state.current_page > 1:
        st.session_state.current_page -= 1

with col2:
    st.markdown(f"<h6 style='text-align: center;'>Trang {st.session_state.current_page} / {total_pages}</h6>", unsafe_allow_html=True)

with col3:
    if st.button("Tiếp ➡️", use_container_width=True) and st.session_state.current_page < total_pages:
        st.session_state.current_page += 1

# 🔎 Cắt danh sách tool theo trang hiện tại
start_idx = (st.session_state.current_page - 1) * TOOLS_PER_PAGE
end_idx = start_idx + TOOLS_PER_PAGE
tools_on_page = filtered_tools[start_idx:end_idx]

# 🧱 Hiển thị tool theo dạng lưới
num_rows = ceil(len(tools_on_page) / COLS_PER_ROW)
for row in range(num_rows):
    cols = st.columns(COLS_PER_ROW)
    for i in range(COLS_PER_ROW):
        index = row * COLS_PER_ROW + i
        if index >= len(tools_on_page):
            break

        tool = tools_on_page[index]
        name = tool["name"]
        enabled = tool["enabled"]

        with cols[i]:
            with st.container(border=True):
                st.checkbox("Chọn", key=f"chk_{name}")
                st.markdown(f"**Tên tool:** {name}")
                st.toggle("Kích hoạt", value=enabled, key=f"toggle_{name}")
