# FastMCP Swagger Server

This example demonstrates how to expose one or more OpenAPI specifications through the [FastMCP](https://pypi.org/project/fastmcp/) server. Each Swagger file is loaded and its endpoints are registered as MCP tools.

## Requirements

- Python 3.12
- `fastmcp` package (`pip install fastmcp`)

## Usage

```bash
pip install -r requirements.txt  # install dependencies
python server.py [config.json or URL]
```

Alternatively set the `CONFIG_URL` environment variable to a file path or URL
before running the server.

By default the server listens on port `3000`. Each Swagger file becomes its own MCP server mounted under its configured `prefix`. SSE connections for a spec are available at `/<prefix>/sse` with messages posted to `/<prefix>/messages`. A combined server exposing all tools is also mounted at `/sse` and `/messages`. A simple health check is available at `/health`.

The OpenAPI schemas to load are configured in `config.json`. Multiple specifications can be provided using the `swagger` array. Each entry requires either a `file` or `url`, an `apiBaseUrl` and a unique `prefix` used for the mount paths.

Example `config.json`:

```json
{
  "swagger": [
    {
      "file": "examples/swagger-pet-store.json",
      "apiBaseUrl": "https://petstore.swagger.io/v2",
      "prefix": "petstore"
    },
    {
      "url": "https://example.com/other-openapi.json",
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

Additional Swagger files can be added to the `swagger` list with different prefixes to combine multiple APIs into one MCP server. For example, a prefix of `petstore` will expose endpoints at `/petstore/sse` and `/petstore/messages`.
