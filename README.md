# Smart 智能一体 Agent 助手

Smart 是一个结合企业内部多系统和多功能智能体 (Agent) 的统一入口。系统基于 FastAPI 提供 Web/API 访问, 使用 LangChain 协调 LLM (默认支持 LLaMA/Ollama 与 OpenAI), 并通过 Model Context Protocol (MCP) 访问日程、工时、权限和差旅系统。

该示例聚焦于 Agent 协调层和 MCP 调用的工程实现, 便于在本地快速运行与二次开发。生产环境可在此基础上接入真实的 MCP 服务、企业身份认证和审计链路。

## 架构概述

```text
┌────────────────────────────────────────┐
│            企业 Portal / Chat UI       │
└────────────────────────────────────────┘
                    │ FastAPI (REST/WebSocket)
                    ▼
┌────────────────────────────────────────┐
│        Smart Agent Orchestrator │
│  • LangChain Planner + LLM (LLaMA/OpenAI)│
│  • 工具注册中心 + MCP 调用封装             │
└────────────────────────────────────────┘
        │calendar  │timesheet │access │travel
        ▼          ▼          ▼       ▼
┌────────────┐┌────────────┐┌────────────┐┌────────────┐
│ MCP 日程系统 ││ MCP 工时系统 ││ MCP 权限系统 ││ MCP 差旅系统 │
└────────────┘└────────────┘└────────────┘└────────────┘
```

### 模块说明

- **入口层 (FastAPI)**: 提供统一 REST 入口 `/api/v1/agent/chat`, 未来可扩展为 WebSocket 对话。
- **Agent 协调层**: `SmartFlowAgent` 负责接收请求 → 调用 Planner → 按步骤执行 MCP 工具 → 使用 LLM 生成自然语言回复。
- **Planner**: 默认实现为规则驱动, 实际环境中可替换为基于 LangChain 的自主规划智能体 (ReAct/ToolFormer 等)。
- **LLM 层**: `LocalTemplateLLM` (纯模板, 无需联网)、`OllamaLLM` (支持本地 LLaMA 模型)、`OpenAILLM` (支持 OpenAI GPT)。
- **MCP 工具封装**: `CalendarBookingTool`、`TimesheetTool`、`AccessManagementTool`、`TravelApprovalTool` 分别指向不同的企业系统, 默认通过 `MockMCPClient` 模拟返回。

## 快速开始

### 1. 安装依赖

```bash
cd smartflow_agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 启动服务

默认使用本地模板 LLM 和 Mock MCP, 适用于开发测试:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 发起请求

```bash
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我预订明天下午三点的会议室",
    "user_id": "u123456"
  }'
```

返回示例:

```json
{
  "message": "以下是根据您的请求自动执行的结果:\n用户输入: 帮我预订明天下午三点的会议室\n执行计划: - calendar(book_meeting_room): Simulated calendar.book_meeting_room executed with payload: {'raw_user_input': '帮我预订明天下午三点的会议室', 'user_id': 'u123456'}\n如需进一步操作, 请继续告诉我。",
  "plan": {
    "steps": [
      {
        "tool_name": "calendar",
        "action": "book_meeting_room",
        "parameters": {
          "raw_user_input": "帮我预订明天下午三点的会议室"
        },
        "reasoning": "用户希望预订会议室, 需要调用日程系统。"
      }
    ],
    "confidence": 1.0
  },
  "mcp_results": [
    {
      "tool_name": "calendar",
      "action": "book_meeting_room",
      "payload": {
        "namespace": "calendar",
        "action": "book_meeting_room",
        "payload": {
          "raw_user_input": "帮我预订明天下午三点的会议室",
          "user_id": "u123456"
        }
      },
      "human_readable": "Simulated calendar.book_meeting_room executed with payload: {'raw_user_input': '帮我预订明天下午三点的会议室', 'user_id': 'u123456'}"
    }
  ],
  "generated_at": "2024-01-01T00:00:00"
}
```

## 切换至真实 LLM / MCP

### 使用 OpenAI 模型

```bash
export SMARTFLOW_LLM_PROVIDER=openai
export SMARTFLOW_OPENAI_API_KEY=sk-***
export SMARTFLOW_OPENAI_MODEL=gpt-4o-mini  # 可选
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 使用本地 Ollama (LLaMA)

```bash
export SMARTFLOW_LLM_PROVIDER=ollama
export SMARTFLOW_OLLAMA_MODEL=llama3
export SMARTFLOW_OLLAMA_ENDPOINT=http://127.0.0.1:11434
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 接入企业 MCP 服务

将 `build_tools` 方法中的 `MockMCPClient` 替换为 `HTTPMCPClient`, 并配置实际的网关地址、认证头等逻辑。所有工具均复用 `invoke(namespace, action, payload)` 接口, 方便统一治理和审计。

```python
from app.mcp.client import HTTPMCPClient

client = HTTPMCPClient(base_url="https://mcp.your-company.internal")
```

## 目录结构

```text
smartflow_agent/
├── README.md
├── requirements.txt
└── app
    ├── __init__.py
    ├── agents
    │   └── orchestrator.py
    ├── config
    │   └── settings.py
    ├── main.py
    ├── mcp
    │   ├── __init__.py
    │   ├── client.py
    │   └── tools.py
    ├── schemas
    │   ├── __init__.py
    │   └── agent.py
    └── services
        ├── __init__.py
        ├── llm.py
        ├── planner.py
        └── prompt_templates.py
```

## 测试策略建议

- 引入 `pytest` + `httpx.AsyncClient` 编写端到端用例, 校验 Planner → MCP → LLM 流程。
- 使用 LangChain 的 `ToolExecutor` 将 MCP 工具注册为工具 (Tool), 支持基于 ReAct 的多轮规划。
- 在真实环境中启用审计日志、链路追踪与异常告警 (Prometheus/Grafana)。

## 下一步规划

1. **对话上下文记忆**: 结合向量数据库 (Milvus/PGVector) 存储历史任务上下文。
2. **流程编排引擎**: 将复杂流程编排为 BPMN/State Machine, 与 Agent 协同。
3. **权限与安全**: 整合企业 OAuth / Zero Trust, 实现最小权限调用 MCP。
4. **可视化运营后台**: 实时观察流程状态、重试和手动干预能力。

## 许可证

本示例以 MIT 许可证开源, 可自由用于企业内部落地。
