from enum import Enum


class RuntimeTool(Enum):
    BROWSER = 'browser'


def add_browser_tool(cls):
    cls.runtime_tools = [RuntimeTool.BROWSER]
    return cls
