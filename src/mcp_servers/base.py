from abc import ABC, abstractmethod

from pydantic import BaseModel


class MCPRequest(BaseModel):
    query: str
    context: dict | None = None


class MCPResponse(BaseModel):
    content: str
    source: str
    metadata: dict | None = None


class MCPServer(ABC):
    @abstractmethod
    async def handle(self, request: MCPRequest) -> MCPResponse:
        ...
