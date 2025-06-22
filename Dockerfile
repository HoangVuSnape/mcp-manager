FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app/fastmcp_server
ADD . /app
RUN uv sync --locked
CMD ["uv","--directory","/app/fastmcp_server", "run", "server.py"]
