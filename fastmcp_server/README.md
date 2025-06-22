# FastMCP Swagger Server

This example demonstrates how to expose one or more OpenAPI specifications through the [FastMCP](https://pypi.org/project/fastmcp/) server. Each Swagger specification is loaded from a local path or URL and its endpoints are registered as MCP tools.

## Requirements

- Python 3.12
- `fastmcp` package (`pip install fastmcp`)

## Usage

```bash
pip install -r requirements.txt  # install dependencies
python server.py [config.json or URL]
```

### Running tests

```bash
pytest
```

Alternatively set the `CONFIG_URL` environment variable to a file path or URL
before running the server.

Multiple config files can be provided by separating paths with commas or by
setting the `EXTRA_CONFIGS` environment variable. Set `DB_URL` to a PostgreSQL
connection string to store or retrieve the loaded configuration. The current
configuration can be written to disk by setting the `EXPORT_CONFIG` environment
variable to a file path.

### Docker Compose

The repository includes a `docker-compose.yml` that starts the server
alongside a PostgreSQL instance. Build and run the services with:

```bash
docker compose up --build
```

The default configuration is loaded from `fastmcp_server/config.json` and
stored in the `db` service. The server is available on `http://localhost:3000`.

By default the server listens on port `3000`. Each Swagger specification becomes its own MCP server mounted under its configured `prefix`. SSE connections for a spec are available at `/<prefix>/sse` with messages posted to `/<prefix>/messages`. A combined server exposing all tools is also mounted at `/sse` and `/messages`. A simple health check is available at `/health` and the list of available prefixes can be retrieved from `/list-server`.

When the server starts it prints a short summary of how many tools were loaded for each Swagger specification and the total number of tools across all specs:

```
Loaded N Swagger servers:
  - prefix1: X tools
  - prefix2: Y tools
Total tools available: Z
```

The OpenAPI schemas to load are configured in `config.json`. Multiple specifications can be provided using the `swagger` array. Each entry must include a `path` pointing to either a local file or a remote URL, an `apiBaseUrl` and a unique `prefix` used for the mount paths.

Example `config.json`:

```json
{
  "swagger": [
    {
      "path": "examples/swagger-pet-store.json",
      "apiBaseUrl": "https://petstore.swagger.io/v2",
      "prefix": "petstore"
    },
    {
      "path": "https://example.com/other-openapi.json",
      "apiBaseUrl": "https://example.com/api",
      "prefix": "remote"
    }
  ],
  "server": {
    "host": "0.0.0.0",
    "port": 3000
  }
}
```

Additional Swagger specifications can be added to the `swagger` list with different prefixes to combine multiple APIs into one MCP server. For example, a prefix of `petstore` will expose endpoints at `/petstore/sse` and `/petstore/messages`.
