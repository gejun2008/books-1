from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    role: str = Field(description="Originator of the message, e.g. user/assistant/system")
    content: str = Field(description="Content of the message")


class MCPInvocationResult(BaseModel):
    tool_name: str = Field(description="Identifier of the MCP tool that produced the output")
    action: str = Field(description="Action executed against the enterprise system")
    payload: dict[str, Any] = Field(default_factory=dict, description="Raw response payload from MCP")
    human_readable: str = Field(description="Human friendly summary returned by the tool")


class AgentPlanStep(BaseModel):
    tool_name: str = Field(description="Tool selected for this step")
    action: str = Field(description="Concrete action to execute on the tool")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameters passed to the tool")
    reasoning: str = Field(description="Explanation of why the tool/action was selected")


class AgentPlan(BaseModel):
    steps: list[AgentPlanStep] = Field(default_factory=list, description="Ordered plan steps")
    confidence: float = Field(default=1.0, description="Planner confidence between 0 and 1")


class AgentChatRequest(BaseModel):
    message: str = Field(description="Latest message from the end user")
    user_id: str = Field(description="Identifier of the employee making the request")
    history: list[AgentMessage] = Field(default_factory=list, description="Optional message history for context")


class AgentChatResponse(BaseModel):
    message: str = Field(description="Agent response presented to the end user")
    plan: AgentPlan = Field(description="Plan executed by the agent")
    mcp_results: list[MCPInvocationResult] = Field(
        default_factory=list, description="Outputs returned by downstream MCP tools"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the response")


class HealthCheck(BaseModel):
    status: str = Field(description="health status string")
