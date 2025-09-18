from pydantic import BaseSettings, Field


class SmartFlowSettings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = Field(default="C-SmartFlow Agent Gateway", description="FastAPI application name")
    api_prefix: str = Field(default="/api/v1/agent", description="Base API prefix for agent endpoints")

    llm_provider: str = Field(
        default="local",
        description="LLM provider identifier. Supported: local, openai, ollama",
    )
    openai_api_key: str | None = Field(default=None, description="API key for OpenAI completion models")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI chat model name")

    ollama_model: str = Field(default="llama3", description="Model name exposed by a local Ollama server")
    ollama_endpoint: str = Field(default="http://127.0.0.1:11434", description="Ollama server URL")

    planner_confidence_threshold: float = Field(
        default=0.5,
        description="Minimum confidence required for planner decisions when using LLM-based planning.",
    )

    class Config:
        env_prefix = "SMARTFLOW_"
        case_sensitive = False


def get_settings() -> SmartFlowSettings:
    """Helper for lazy settings import."""

    return SmartFlowSettings()
