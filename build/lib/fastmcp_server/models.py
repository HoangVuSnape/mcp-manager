from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Simple status response."""

    status: str


class ListServersResponse(BaseModel):
    """Response model for list-server."""

    servers: list[str]


class ListToolsResponse(BaseModel):
    """Response model for list-tools."""

    tools: list[str]


class AddServerRequest(BaseModel):
    """Request body for adding a Swagger spec."""

    path: str
    apiBaseUrl: str
    prefix: str | None = None


class AddServerResponse(BaseModel):
    """Response after adding a Swagger spec."""

    added: str
    tools: int


class ToolEnabledRequest(BaseModel):
    """Request body for enabling/disabling a tool."""

    prefix: str
    name: str
    enabled: bool = False


class ToolEnabledResponse(BaseModel):
    """Response for tool-enabled state."""

    tool: str
    enabled: bool


class SearchEnabledRequest(BaseModel):
    """Request body for enabling/disabling search for a server."""

    prefix: str
    enabled: bool = False


class SearchEnabledResponse(BaseModel):
    """Response for search-enabled state."""

    prefix: str
    enabled: bool


class SearchResult(BaseModel):
    """Single search result containing prefix and tool name."""

    prefix: str
    tool: str


class SearchResponse(BaseModel):
    """Response model for search endpoint."""

    results: list[SearchResult]
