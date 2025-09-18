from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..schemas.agent import AgentPlan, AgentPlanStep


@dataclass(slots=True)
class PlannerRule:
    keywords: tuple[str, ...]
    tool_name: str
    action: str
    reasoning: str


class RuleBasedPlanner:
    """A light-weight planner that maps keywords to MCP tools.

    In production the planner can be replaced with a LangChain agent leveraging the selected LLM
    to dynamically design multi-step workflows. This implementation keeps the project runnable
    without external dependencies while still demonstrating the orchestration layer.
    """

    def __init__(self, rules: Iterable[PlannerRule]) -> None:
        self._rules = list(rules)

    async def plan(self, *, message: str) -> AgentPlan:
        lowered = message.lower()
        steps: list[AgentPlanStep] = []
        for rule in self._rules:
            if any(keyword in lowered for keyword in rule.keywords):
                steps.append(
                    AgentPlanStep(
                        tool_name=rule.tool_name,
                        action=rule.action,
                        parameters={"raw_user_input": message},
                        reasoning=rule.reasoning,
                    )
                )
        confidence = 1.0 if steps else 0.3
        return AgentPlan(steps=steps, confidence=confidence)
