from pydantic import BaseModel, Field
from typing import List, Optional

class Pet(BaseModel):
    """Request model for calling a tool."""
    id: int
    name: str
    
class InfoTool(BaseModel):
    """Information about a tool."""
    tool: str
