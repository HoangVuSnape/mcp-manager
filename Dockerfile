FROM python:3.12-slim
WORKDIR /app
COPY fastmcp_server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY fastmcp_server/ ./
CMD ["python", "server.py"]
