from abc import ABC
from logging import Logger
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Callable


class BaseAgent(ABC):
    def __init__(self, name: str, llm: BaseChatModel, tools: list[Callable]):
        self.name = name
        self.llm = llm
        self.tools = tools
        self.logger = Logger(self.name)
