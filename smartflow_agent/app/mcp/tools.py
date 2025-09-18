from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .client import MCPClient


@dataclass(slots=True)
class ToolExecutionContext:
    user_id: str


@dataclass(slots=True)
class ToolRequest:
    action: str
    parameters: dict[str, Any]
    context: ToolExecutionContext


@dataclass(slots=True)
class ToolResponse:
    payload: dict[str, Any]
    human_readable: str


class BaseMCPTool:
    name: str

    def __init__(self, *, namespace: str, client: MCPClient) -> None:
        self.namespace = namespace
        self.client = client

    async def execute(self, request: ToolRequest) -> ToolResponse:
        payload = {**request.parameters, "user_id": request.context.user_id}
        raw_response = await self.client.invoke(namespace=self.namespace, action=request.action, payload=payload)
        return ToolResponse(payload=raw_response.get("result", {}), human_readable=raw_response.get("summary", ""))


class CalendarBookingTool(BaseMCPTool):
    name = "calendar"


class TimesheetTool(BaseMCPTool):
    name = "timesheet"


class AccessManagementTool(BaseMCPTool):
    name = "access"


class TravelApprovalTool(BaseMCPTool):
    name = "travel"
