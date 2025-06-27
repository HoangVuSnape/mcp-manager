FROM python:3.12-slim

WORKDIR /app

# Cài gói cần thiết (tối thiểu để tránh lỗi wget ở healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để tối ưu layer
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn
COPY . .

# Expose MCP server port và Streamlit port
EXPOSE 8000 8501

# Mặc định (sẽ bị override bởi docker-compose command)
CMD ["streamlit", "run", "app.py"]
