from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SpanType(Enum):
    INITIALIZATION = 'init'  # FIXME: check if this is the right type
    IMPLEMENTATION = 'impl'
    DOCUMENTATION = 'docs'


class CodeBlockType(Enum):
    MODULE = 'Module'
    CLASS = 'Class'
    CONSTRUCTOR = 'Constructor'
    FUNCTION = 'Function'
    STATEMENT = 'Statement'
    IMPORT = 'Import'
    EXPORT = 'Export'
    CALL = 'Call'
    ASSIGNMENT = 'Assignment'
    TEST_SUITE = 'TestSuite'
    TEST_CASE = 'TestCase'
    COMMENT = 'Comment'
    CODE = 'Code'  # Default type for code blocks

    @classmethod
    def from_str(cls, tag: str) -> Optional['CodeBlockType']:
        if not tag.startswith('definition'):
            return None

        tag_to_block_type = {
            'definition.assignment': cls.ASSIGNMENT,
            'definition.call': cls.CALL,
            'definition.class': cls.CLASS,
            'definition.code': cls.CODE,
            'definition.constructor': cls.CONSTRUCTOR,
            'definition.comment': cls.COMMENT,
            'definition.export': cls.EXPORT,
            'definition.function': cls.FUNCTION,
            'definition.import': cls.IMPORT,
            'definition.module': cls.MODULE,
            'definition.statement': cls.STATEMENT,
            'definition.test_case': cls.TEST_CASE,
            'definition.test_suite': cls.TEST_SUITE,
        }
        return tag_to_block_type.get(tag)


class CodeBlockSpan(BaseModel):
    """
    A `CodeBlockSpan` is a representation of a span of code in an arbitrary code file.
    """

    span_id: str = Field()
    span_type: SpanType = Field(description='The type of the span')
    start_line: int = Field(description='The start line of the span')
    end_line: int = Field(description='The end line of the span')


class CodeBlock(BaseModel):
    """
    A `CodeBlock` is a representation of a code block. It can contains multiple `CodeBlockSpan`s.
    """

    content: str = Field(description='The content of the code block')
    block_type: CodeBlockType = Field(description='The type of the code block')
