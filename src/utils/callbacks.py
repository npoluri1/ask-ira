import os

from langchain_core.callbacks import BaseCallbackHandler

from src.config import get_settings

settings = get_settings()


class LangSmithTracer(BaseCallbackHandler):
    def __init__(self, project_name: str = "ask-ira"):
        self.project_name = project_name

    @property
    def always_verbose(self) -> bool:
        return True

    def on_llm_start(self, serialized: dict, prompts: list[str], **kwargs):
        pass

    def on_chain_start(self, serialized: dict, inputs: dict, **kwargs):
        pass

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
        pass


def configure_langsmith() -> None:
    if settings.langsmith_tracing and settings.langsmith_api_key:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_ENDPOINT", settings.langsmith_endpoint)
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)
