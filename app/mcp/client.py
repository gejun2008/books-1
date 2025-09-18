from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class MCPTransportError(RuntimeError):
    """Raised when MCP call fails."""


class MCPClient(Protocol):
    async def invoke(self, *, namespace: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Invoke an MCP tool exposed by an enterprise system."""


@dataclass(slots=True)
class HTTPMCPClient:
    """Minimal MCP client over HTTP using Model Context Protocol semantics.

    The real implementation inside the enterprise can reuse the same interface. This example
    assumes every MCP service exposes a POST endpoint at ``/{namespace}/{action}`` and returns
    JSON payloads containing ``result`` and ``summary`` fields.
    """

    base_url: str
    timeout: float = 10.0

    async def invoke(self, *, namespace: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(f"/{namespace}/{action}", json=payload)
            if response.status_code >= 400:
                raise MCPTransportError(f"MCP call failed with status {response.status_code}: {response.text}")
            return response.json()


class MockMCPClient:
    """In-memory MCP client used for local development and automated testing."""

    async def invoke(self, *, namespace: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        # In a real implementation this would not exist. We keep mock responses deterministic.
        summary = f"Simulated {namespace}.{action} executed with payload: {payload}."
        return {
            "result": {
                "namespace": namespace,
                "action": action,
                "payload": payload,
            },
            "summary": summary,
        }
