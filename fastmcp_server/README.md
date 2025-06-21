# FastMCP Swagger Server

This example demonstrates how to expose one or more OpenAPI specifications through the [FastMCP](https://pypi.org/project/fastmcp/) server. Each Swagger file is loaded and its endpoints are registered as MCP tools.

## Requirements

- Python 3.12
- `fastmcp` package (`pip install fastmcp`)

## Usage

```bash
pip install -r requirements.txt  # install dependencies
python server.py                 # start the server
```

By default the server listens on port `3000` and serves SSE connections at `/sse` with messages posted to `/messages`. A simple health check is available at `/health`.

The OpenAPI schemas to load are configured in `config.json`. Multiple specifications can be provided using the `swagger` array. Each entry requires a `file`, `apiBaseUrl` and a unique `prefix` used when mounting the tools.

Example `config.json`:

```json
{
  "swagger": [
    {
      "file": "examples/swagger-pet-store.json",
      "apiBaseUrl": "https://petstore.swagger.io/v2",
      "prefix": "petstore"
    }
  ],
  "server": {
    "host": "0.0.0.0",
    "port": 3000
  }
}
```

Additional Swagger files can be added to the `swagger` list with different prefixes to combine multiple APIs into one MCP server.
