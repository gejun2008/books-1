from __future__ import annotations

from typing import Any

from ..mcp.tools import BaseMCPTool, ToolExecutionContext, ToolRequest
from ..schemas.agent import AgentChatRequest, AgentChatResponse, MCPInvocationResult
from ..services.llm import BaseLLMService
from ..services.planner import RuleBasedPlanner


class SmartFlowAgent:
    """High level orchestration layer that coordinates planning, tool execution and language generation."""

    def __init__(
        self,
        *,
        planner: RuleBasedPlanner,
        llm_service: BaseLLMService,
        tools: dict[str, BaseMCPTool],
    ) -> None:
        self._planner = planner
        self._llm = llm_service
        self._tools = tools

    async def handle(self, request: AgentChatRequest) -> AgentChatResponse:
        plan = await self._planner.plan(message=request.message)

        execution_context = ToolExecutionContext(user_id=request.user_id)
        mcp_results: list[MCPInvocationResult] = []

        for step in plan.steps:
            tool = self._tools.get(step.tool_name)
            if tool is None:
                continue
            tool_request = ToolRequest(action=step.action, parameters=step.parameters, context=execution_context)
            tool_response = await tool.execute(tool_request)
            mcp_results.append(
                MCPInvocationResult(
                    tool_name=step.tool_name,
                    action=step.action,
                    payload=tool_response.payload,
                    human_readable=tool_response.human_readable,
                )
            )

        llm_context: dict[str, Any] = {
            "plan": [
                {
                    "tool_name": result.tool_name,
                    "action": result.action,
                    "summary": result.human_readable,
                }
                for result in mcp_results
            ],
            "raw_plan": plan.dict(),
        }
        response_message = await self._llm.generate_response(user_input=request.message, context=llm_context)

        return AgentChatResponse(message=response_message, plan=plan, mcp_results=mcp_results)


def build_default_agent(*, planner: RuleBasedPlanner, llm_service: BaseLLMService, tools: dict[str, BaseMCPTool]) -> SmartFlowAgent:
    return SmartFlowAgent(planner=planner, llm_service=llm_service, tools=tools)
