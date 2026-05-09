from langchain_core.callbacks import BaseCallbackHandler

from src.config import get_settings

settings = get_settings()


class LangSmithTracer(BaseCallbackHandler):
    def __init__(self, project_name: str = "ask-ira"):
        self.project_name = project_name

    @property
    def always_verbose(self) -> bool:
        return True
