from __future__ import annotations

from fastapi import Depends, FastAPI

from .agents.orchestrator import SmartFlowAgent, build_default_agent
from .config.settings import SmartFlowSettings, get_settings
from .mcp.client import MockMCPClient
from .mcp.tools import AccessManagementTool, CalendarBookingTool, TimesheetTool, TravelApprovalTool
from .schemas.agent import AgentChatRequest, AgentChatResponse, HealthCheck
from .services.llm import build_llm_service
from .services.planner import PlannerRule, RuleBasedPlanner


def build_planner(settings: SmartFlowSettings) -> RuleBasedPlanner:
    rules = [
        PlannerRule(
            keywords=("meeting", "room", "会议", "预订"),
            tool_name=CalendarBookingTool.name,
            action="book_meeting_room",
            reasoning="用户希望预订会议室, 需要调用日程系统。",
        ),
        PlannerRule(
            keywords=("timesheet", "工时", "填报"),
            tool_name=TimesheetTool.name,
            action="submit_timesheet",
            reasoning="用户需要完成工时填报, 由工时系统处理。",
        ),
        PlannerRule(
            keywords=("权限", "access", "vpn"),
            tool_name=AccessManagementTool.name,
            action="request_access",
            reasoning="用户请求访问权限, 需要权限系统审批。",
        ),
        PlannerRule(
            keywords=("差旅", "travel", "机票", "酒店"),
            tool_name=TravelApprovalTool.name,
            action="request_travel",
            reasoning="用户发起差旅审批, 需调用差旅系统。",
        ),
    ]
    return RuleBasedPlanner(rules)


def build_tools(settings: SmartFlowSettings) -> dict[str, CalendarBookingTool]:
    # In production, inject HTTPMCPClient with authenticated transport.
    client = MockMCPClient()
    return {
        CalendarBookingTool.name: CalendarBookingTool(namespace="calendar", client=client),
        TimesheetTool.name: TimesheetTool(namespace="timesheet", client=client),
        AccessManagementTool.name: AccessManagementTool(namespace="access", client=client),
        TravelApprovalTool.name: TravelApprovalTool(namespace="travel", client=client),
    }


def build_agent(settings: SmartFlowSettings = Depends(get_settings)) -> SmartFlowAgent:
    planner = build_planner(settings)
    llm_service = build_llm_service(settings.llm_provider, settings=settings)
    tools = build_tools(settings)
    return build_default_agent(planner=planner, llm_service=llm_service, tools=tools)


def create_app(settings: SmartFlowSettings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/health", response_model=HealthCheck)
    async def health() -> HealthCheck:  # pragma: no cover - trivial
        return HealthCheck(status="ok")

    agent = build_agent(settings)

    @app.post(f"{settings.api_prefix}/chat", response_model=AgentChatResponse)
    async def chat(payload: AgentChatRequest) -> AgentChatResponse:
        return await agent.handle(payload)

    return app


app = create_app()
