import os

from utils import load_file

PROMPT_DIR = os.path.dirname(__file__)
TEMPLATE_WITH_TOOL = load_file(os.path.join(PROMPT_DIR, 'template_with_tool.txt'))


class PromptTemplate:
    """A prompt template."""

    def __init__(self, template: str):
        self.template: str = template

    def __call__(self, **kwargs) -> str:
        return self.template.format(**kwargs)


class ToolPromptTemplate(PromptTemplate):
    def __init__(self, use_tool: bool):
        if use_tool:
            template = TEMPLATE_WITH_TOOL
        else:
            raise NotImplementedError('Evaluation without tool is not supported yet.')
        super().__init__(template)
