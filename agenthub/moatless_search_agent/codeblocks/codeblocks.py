import re
from enum import Enum
from typing import Any, List, Optional, Set

from pydantic import BaseModel, Field, root_validator, validator
from typing_extensions import deprecated

from .parser.comment import get_comment_symbol

BlockPath = List[str]


class SpanMarker(Enum):
    TAG = 1
    COMMENT = 2


class CodeBlockTypeGroup(str, Enum):
    STRUCTURE = 'Structures'
    IMPLEMENTATION = 'Implementation'
    IMPORT = 'Imports'

    BLOCK_DELIMITER = 'BlockDelimiter'
    SPACE = 'Space'

    COMMENT = 'Comment'

    ERROR = 'Error'


class CodeBlockType(Enum):
    MODULE = (
        'Module',
        CodeBlockTypeGroup.STRUCTURE,
    )  # TODO: Module shouldn't be a STRUCTURE
    CLASS = ('Class', CodeBlockTypeGroup.STRUCTURE)
    FUNCTION = ('Function', CodeBlockTypeGroup.STRUCTURE)

    # TODO: Remove and add sub types to functions and classes
    CONSTRUCTOR = ('Constructor', CodeBlockTypeGroup.STRUCTURE)
    TEST_SUITE = ('TestSuite', CodeBlockTypeGroup.STRUCTURE)
    TEST_CASE = ('TestCase', CodeBlockTypeGroup.STRUCTURE)

    IMPORT = ('Import', CodeBlockTypeGroup.IMPORT)

    EXPORT = ('Export', CodeBlockTypeGroup.IMPLEMENTATION)
    COMPOUND = ('Compound', CodeBlockTypeGroup.IMPLEMENTATION)
    # Dependent clauses are clauses that are dependent on another compound statement and can't be shown on their own
    DEPENDENT_CLAUSE = ('DependentClause', CodeBlockTypeGroup.IMPLEMENTATION)
    ASSIGNMENT = ('Assignment', CodeBlockTypeGroup.IMPLEMENTATION)
    CALL = ('Call', CodeBlockTypeGroup.IMPLEMENTATION)
    STATEMENT = ('Statement', CodeBlockTypeGroup.IMPLEMENTATION)

    CODE = ('Code', CodeBlockTypeGroup.IMPLEMENTATION)

    # TODO: Incorporate in code block?
    BLOCK_DELIMITER = ('BlockDelimiter', CodeBlockTypeGroup.BLOCK_DELIMITER)

    # TODO: Remove as it's just to fill upp spaces at the end of the file?
    SPACE = ('Space', CodeBlockTypeGroup.SPACE)

    COMMENT = ('Comment', CodeBlockTypeGroup.COMMENT)
    COMMENTED_OUT_CODE = (
        'Placeholder',
        CodeBlockTypeGroup.COMMENT,
    )  # TODO: Replace to PlaceholderComment

    ERROR = ('Error', CodeBlockTypeGroup.ERROR)

    def __init__(self, value: str, group: CodeBlockTypeGroup):
        self._value_ = value  # type: ignore
        self.group = group

    @classmethod
    def from_string(cls, tag: str) -> Optional['CodeBlockType']:
        if not tag.startswith('definition'):
            return None

        tag_to_block_type = {
            'definition.assignment': cls.ASSIGNMENT,
            'definition.block_delimiter': cls.BLOCK_DELIMITER,
            'definition.call': cls.CALL,
            'definition.class': cls.CLASS,
            'definition.code': cls.CODE,
            'definition.comment': cls.COMMENT,
            'definition.compound': cls.COMPOUND,
            'definition.constructor': cls.CONSTRUCTOR,
            'definition.dependent_clause': cls.DEPENDENT_CLAUSE,
            'definition.error': cls.ERROR,
            'definition.export': cls.EXPORT,
            'definition.function': cls.FUNCTION,
            'definition.import': cls.IMPORT,
            'definition.module': cls.MODULE,
            'definition.statement': cls.STATEMENT,
            'definition.test_suite': cls.TEST_SUITE,
            'definition.test_case': cls.TEST_CASE,
        }
        return tag_to_block_type.get(tag)


NON_CODE_BLOCKS = [
    CodeBlockType.BLOCK_DELIMITER,
    CodeBlockType.COMMENT,
    CodeBlockType.COMMENTED_OUT_CODE,
    CodeBlockType.EXPORT,
    CodeBlockType.IMPORT,
    CodeBlockType.ERROR,
    CodeBlockType.SPACE,
]

INDEXED_BLOCKS = [
    CodeBlockType.FUNCTION,
    CodeBlockType.CLASS,
    CodeBlockType.TEST_SUITE,
    CodeBlockType.TEST_CASE,
]


@deprecated('Use BlockSpans to define code block visibility instead')
class PathTree(BaseModel):
    show: bool = Field(default=False, description='Show the block and all sub blocks.')
    tree: dict[str, 'PathTree'] = Field(default_factory=dict)

    @staticmethod
    def from_block_paths(block_paths: List[BlockPath]) -> 'PathTree':
        tree = PathTree()
        for block_path in block_paths:
            tree.add_to_tree(block_path)

        return tree

    def child_tree(self, key: str | None) -> Optional['PathTree']:
        if not key:
            return None
        return self.tree.get(key, None)

    def merge(self, other: 'PathTree'):
        if other.show:
            self.show = True

        for key, value in other.tree.items():
            if key not in self.tree:
                self.tree[key] = PathTree()
            self.tree[key].merge(value)

    def extend_tree(self, paths: list[list[str]]):
        for path in paths:
            self.add_to_tree(path)

    def add_to_tree(self, path: list[str]):
        # if path is None:
        #     return

        if len(path) == 0:
            self.show = True
            return

        if len(path) == 1:
            if path[0] not in self.tree:
                self.tree[path[0]] = PathTree(show=True)
            else:
                self.tree[path[0]].show = True

            return

        if path[0] not in self.tree:
            self.tree[path[0]] = PathTree(show=False)

        self.tree[path[0]].add_to_tree(path[1:])


class ReferenceScope(str, Enum):
    EXTERNAL = 'external'
    DEPENDENCY = 'dependency'  # External dependency
    FILE = 'file'  # File in repository
    PROJECT = 'project'
    CLASS = 'class'
    LOCAL = 'local'
    GLOBAL = 'global'


class RelationshipType(str, Enum):
    UTILIZES = 'utilizes'
    USES = 'uses'
    DEFINED_BY = 'defined_by'
    IS_A = 'is_a'
    PROVIDES = 'provides'
    IMPORTS = 'imports'
    CALLS = 'calls'
    DEPENDENCY = 'dependency'
    TYPE = 'type'


class Relationship(BaseModel):
    scope: ReferenceScope = Field(description='The scope of the reference.')
    identifier: Optional[str] = Field(default=None, description='ID')
    type: RelationshipType = Field(
        default=RelationshipType.USES, description='The type of the reference.'
    )
    external_path: List[str] = Field(
        default=[], description='The path to the referenced parent code block.'
    )
    resolved_path: List[str] = Field(
        default=[], description='The path to the file with the referenced code block.'
    )
    path: List[str] = Field(
        default=[], description='The path to the referenced code block.'
    )

    @root_validator(pre=True)
    def validate_path(cls, values):
        external_path = values.get('external_path')
        path = values.get('path')
        if not external_path and not path:
            raise ValueError('Cannot create Reference without external_path or path.')
        return values

    def __hash__(self):
        return hash((self.scope, tuple(self.path)))

    def __eq__(self, other):
        return (self.scope, self.path) == (other.scope, other.path)

    def full_path(self):
        return self.external_path + self.path

    def __str__(self):
        if self.identifier:
            start_node = self.identifier
        else:
            start_node = ''

        end_node = ''
        if self.external_path:
            end_node = '/'.join(self.external_path)
        if self.path:
            if self.external_path:
                end_node += '/'
            end_node += '.'.join(self.path)

        return f'({start_node})-[:{self.type.name} {{scope: {self.scope.value}}}]->({end_node})'


class Parameter(BaseModel):
    identifier: str = Field(description='The identifier of the parameter.')
    type: Optional[str] = Field(description='The type of the parameter.')


class SpanType(str, Enum):
    INITATION = 'init'
    DOCUMENTATION = 'docs'
    IMPLEMENTATION = 'impl'


class BlockSpan(BaseModel):
    span_id: str = Field()
    span_type: SpanType = Field(description='Type of span.')
    start_line: int = Field(description='Start line of the span.')
    end_line: int = Field(description='End line of the span.')

    initiating_block: 'CodeBlock' = Field(
        default=None,
        description='The block that initiated the span.',
    )

    @property
    def block_type(self):
        return self.initiating_block.type

    # TODO: Remove
    visible: bool = Field(default=True, description='If the span should be visible.')

    index: int = 0

    parent_block_path: BlockPath = Field(
        default=None,
        description='Path to the parent block of the span.',
    )

    is_partial: bool = Field(
        default=False,
        description='If the span is covering a partial part of the parent block.',
    )

    block_paths: List[BlockPath] = Field(
        default=[],
        description='Block paths that should be shown when the span is shown.',
    )

    tokens: int = Field(default=0, description='Number of tokens in the span.')

    def __str__(self):
        return f'{self.span_id} ({self.span_type.value}, {self.tokens} tokens)'

    def get_first_child_block_path(self):
        for block_path in self.block_paths:
            if len(block_path) == len(self.parent_block_path):
                continue
            return block_path


class ValidationError(BaseModel):
    error: str


class CodeBlock(BaseModel):
    content: str
    type: CodeBlockType
    identifier: Optional[str] = None
    parameters: List[Parameter] = []  # TODO: Move to Function sub class
    relationships: List[Relationship] = []
    span_ids: Set[str] = set()
    belongs_to_span: Optional[BlockSpan] = None
    content_lines: List[str] = []
    start_line: int = 0
    end_line: int = 0
    properties: dict = {}
    pre_code: str = ''
    pre_lines: int = 0
    indentation: str = ''
    tokens: int = 0
    children: List['CodeBlock'] = []
    validation_errors: List[ValidationError] = []
    parent: Optional['CodeBlock'] = None
    previous: Optional['CodeBlock'] = None
    next: Optional['CodeBlock'] = None

    @validator('type', pre=True, always=True)
    def validate_type(cls, v):
        if v is None:
            raise ValueError('Cannot create CodeBlock without type.')
        return v

    def __init__(self, **data):
        super().__init__(**data)
        for child in self.children:
            child.parent = self

        if self.pre_code and not re.match(r'^[ \n\\]*$', self.pre_code):
            raise ValueError(
                f'Failed to parse code block with type {self.type} and content `{self.content}`. '
                f'Expected pre_code to only contain spaces and line breaks. Got `{self.pre_code}`'
            )

        if self.pre_code and not self.indentation and not self.pre_lines:
            pre_code_lines = self.pre_code.split('\n')
            self.pre_lines = len(pre_code_lines) - 1
            if self.pre_lines > 0:
                self.indentation = pre_code_lines[-1]
            else:
                self.indentation = self.pre_code

        self.content_lines = self.content.split('\n')
        # if self.indentation and self.pre_lines:
        #    self.content_lines[1:] = [line[len(self.indentation):] for line in self.content_lines[1:]]

    def last(self):
        if self.next:
            return self.next.last()
        return self

    def insert_child(self, index: int, child: 'CodeBlock'):
        if index == 0 and self.children[0].pre_lines == 0:
            self.children[0].pre_lines = 1

        self.children.insert(index, child)
        child.parent = self

    def insert_children(self, index: int, children: List['CodeBlock']):
        for child in children:
            self.insert_child(index, child)
            index += 1

    def append_child(self, child: 'CodeBlock'):
        self.children.append(child)
        self.span_ids.update(child.span_ids)
        child.parent = self

    def append_children(self, children: List['CodeBlock']):
        for child in children:
            self.append_child(child)

    def replace_children(
        self, start_index: int, end_index: int, children: List['CodeBlock']
    ):
        self.children = (
            self.children[:start_index] + children + self.children[end_index:]
        )
        for child in children:
            child.parent = self

    def replace_child(self, index: int, child: 'CodeBlock'):
        # TODO: Do a proper update of everything when replacing child blocks
        child.pre_code = self.children[index].pre_code
        child.pre_lines = self.children[index].pre_lines
        self.sync_indentation(self.children[index], child)

        self.children[index] = child
        child.parent = self

    def remove_child(self, index: int):
        del self.children[index]

    def sync_indentation(self, original_block: 'CodeBlock', updated_block: 'CodeBlock'):
        original_indentation_length = len(original_block.indentation) + len(
            self.indentation
        )
        updated_indentation_length = len(updated_block.indentation) + (
            len(updated_block.parent.indentation) if updated_block.parent else 0
        )

        # To handle separate code blocks provdided out of context
        if (
            original_indentation_length == updated_indentation_length
            and len(updated_block.indentation) == 0
        ):
            updated_block.indentation = ' ' * original_indentation_length

        elif original_indentation_length > updated_indentation_length:
            additional_indentation = ' ' * (
                original_indentation_length - updated_indentation_length
            )
            updated_block.add_indentation(additional_indentation)

    def replace_by_path(self, path: List[str], new_block: 'CodeBlock'):
        if not path:
            return

        for i, child in enumerate(self.children):
            if child.identifier == path[0]:
                if len(path) == 1:
                    self.replace_child(i, new_block)
                    return
                else:
                    child.replace_by_path(path[1:], new_block)

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return self._to_string()

    def sum_tokens(self):
        tokens = self.tokens
        tokens += sum([child.sum_tokens() for child in self.children])
        return tokens

    def get_all_child_blocks(self) -> List['CodeBlock']:
        blocks = []
        for child in self.children:
            blocks.append(child)
            blocks.extend(child.get_all_child_blocks())
        return blocks

    def get_children(self, exclude_blocks: List[CodeBlockType]) -> List['CodeBlock']:
        return [child for child in self.children if child.type not in exclude_blocks]

    def show_related_spans(
        self,
        span_id: Optional[str] = None,  # TODO: Set max tokens to show
    ):
        related_spans = self.find_related_spans(span_id)
        for span in related_spans:
            span.visible = True

    def has_visible_children(self):
        for child in self.children:
            if child.is_visible:
                return True

            if child.has_visible_children():
                return True

        return False

    @property
    def is_visible(self):
        return self.belongs_to_span and self.belongs_to_span.visible

    def _to_string(self) -> str:
        contents = ''

        if self.pre_lines:
            contents += '\n' * (self.pre_lines - 1)
            for i, line in enumerate(self.content_lines):
                if i == 0 and line:
                    contents += '\n' + self.indentation + line
                elif line:
                    contents += '\n' + line
                else:
                    contents += '\n'
        else:
            contents += self.pre_code + self.content

        for i, child in enumerate(self.children):
            contents += child._to_string()

        return contents

    def _build_path_tree(
        self, block_paths: List[str], include_references: bool = False
    ):
        path_tree = PathTree()

        for block_path in block_paths:
            if block_path:
                path = block_path.split('.')
                if include_references:
                    block = self.find_by_path(path)
                    if block:
                        if self.type == CodeBlockType.CLASS:
                            references = [
                                self._fix_reference_path(reference)
                                for reference in self.get_all_relationships(
                                    exclude_types=[
                                        CodeBlockType.FUNCTION,
                                        CodeBlockType.TEST_CASE,
                                    ]
                                )
                                if reference
                                and reference.scope != ReferenceScope.EXTERNAL
                            ]  # FIXME skip _fix_reference_path?
                        else:
                            references = [
                                self._fix_reference_path(reference)
                                for reference in self.get_all_relationships([])
                                if reference
                                and reference.scope != ReferenceScope.EXTERNAL
                            ]  # FIXME skip _fix_reference_path?

                        for ref in references:
                            path_tree.add_to_tree(ref.path)

                path_tree.add_to_tree(path)
            elif block_path == '':
                path_tree.show = True

        return path_tree

    def _to_prompt_string(
        self,
        show_span_id: bool = False,
        span_marker: SpanMarker = SpanMarker.COMMENT,
        show_line_numbers: bool = False,
    ) -> str:
        contents = ''

        if show_span_id:
            contents += '\n\n'
            if span_marker == SpanMarker.COMMENT:
                span_comment = (
                    self.create_comment(f'span_id: {self.belongs_to_span.span_id}')
                    if self.belongs_to_span
                    else ''
                )
                contents += f'{self.indentation}{span_comment}'
            elif span_marker == SpanMarker.TAG:
                contents += (
                    f"\n<span id='{self.belongs_to_span.span_id}'>"
                    if self.belongs_to_span
                    else ''
                )

            if not self.pre_lines:
                contents += '\n'

        def print_line(line_number):
            if not show_line_numbers:
                return ''
            return str(line_number).ljust(6)

        # Just to write out the first line number when there are no pre_lines on first block
        if (
            self.parent
            and self.parent.type == CodeBlockType.MODULE
            and self.parent.children[0] == self
        ):
            contents += print_line(self.start_line)

        if self.pre_lines:
            for i in range(self.pre_lines):
                contents += '\n'
                contents += print_line(self.start_line - self.pre_lines + i + 1)

        contents += self.indentation + self.content_lines[0]

        for i, line in enumerate(self.content_lines[1:]):
            contents += '\n'
            contents += print_line(self.start_line + i + 1)
            contents += line

        return contents

    def to_prompt(
        self,
        span_ids: Optional[Set[str]] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        show_outcommented_code: bool = True,
        outcomment_code_comment: str = '...',
        show_span_id: bool = False,
        current_span_id: Optional[str] = None,
        show_line_numbers: bool = False,
        exclude_block_types: Optional[List[CodeBlockType]] = None,
        include_block_types: Optional[List[CodeBlockType]] = None,
    ):
        contents = ''

        has_outcommented_code = False
        for i, child in enumerate(self.children):
            show_child = True

            if exclude_block_types and child.type in exclude_block_types:
                show_child = False

            if show_child and span_ids:
                show_child = child.has_any_span(span_ids)

            if show_child and include_block_types:
                show_child = child.has_blocks_with_types(include_block_types)

            if show_child and start_line and end_line:
                show_child = child.has_lines(
                    start_line, end_line
                ) or child.is_within_lines(start_line, end_line)

            if show_child:
                if has_outcommented_code:
                    contents += child.create_commented_out_block(
                        outcomment_code_comment
                    ).to_string()

                has_outcommented_code = False

                show_new_span_id = (
                    show_span_id
                    and child.belongs_to_span
                    and (
                        not current_span_id
                        or current_span_id != child.belongs_to_span.span_id
                    )
                )
                if child.belongs_to_span:
                    current_span_id = child.belongs_to_span.span_id

                contents += child._to_prompt_string(
                    show_span_id=bool(show_new_span_id),
                    show_line_numbers=show_line_numbers,
                )
                contents += child.to_prompt(
                    span_ids=span_ids,
                    start_line=start_line,
                    end_line=end_line,
                    show_outcommented_code=show_outcommented_code,
                    outcomment_code_comment=outcomment_code_comment,
                    show_span_id=show_span_id,
                    current_span_id=current_span_id,
                    show_line_numbers=show_line_numbers,
                    exclude_block_types=exclude_block_types,
                    include_block_types=include_block_types,
                )
            elif show_outcommented_code and child.type not in [
                CodeBlockType.COMMENT,
                CodeBlockType.COMMENTED_OUT_CODE,
            ]:
                has_outcommented_code = True

        if (
            outcomment_code_comment
            and has_outcommented_code
            and child.type
            not in [
                CodeBlockType.COMMENT,
                CodeBlockType.COMMENTED_OUT_CODE,
                CodeBlockType.SPACE,
            ]
        ):
            contents += '\n.    ' if show_line_numbers else '\n'
            contents += child.create_commented_out_block(
                outcomment_code_comment
            ).to_string()
            contents += '\n'

        return contents

    def __eq__(self, other):
        if not isinstance(other, CodeBlock):
            return False

        return self.full_path() == other.full_path()

    def find_block_by_type(self, block_type: CodeBlockType) -> Optional['CodeBlock']:
        if self.type == block_type:
            return self

        for child in self.children:
            block = child.find_block_by_type(block_type)
            if block:
                return block

        return None

    def find_type_in_parents(self, block_type: CodeBlockType) -> Optional['CodeBlock']:
        if not self.parent:
            return None

        if self.parent.type == block_type:
            return self.parent

        if self.parent:
            return self.parent.find_type_in_parents(block_type)

        return None

    def find_type_group_in_parents(
        self, block_type_group: CodeBlockTypeGroup
    ) -> Optional['CodeBlock']:
        if not self.parent:
            return None

        if self.parent.type.group == block_type_group:
            return self.parent

        if self.parent:
            return self.parent.find_type_group_in_parents(block_type_group)

        return None

    def find_spans_by_line_numbers(
        self, start_line: int, end_line: Optional[int] = None
    ) -> List[BlockSpan]:
        spans: Any = []
        for child in self.children:
            if end_line is None:
                end_line = start_line

            if child.end_line < start_line:
                continue

            if child.start_line > end_line:
                return spans

            if child.belongs_to_span and child.belongs_to_span.span_id not in spans:
                if (
                    not child.children
                    or child.start_line >= start_line
                    and child.end_line <= end_line
                    or child.start_line == start_line
                    or child.end_line == end_line
                ):
                    spans.append(child.belongs_to_span)

            child_spans = child.find_spans_by_line_numbers(start_line, end_line)
            for span in child_spans:
                if span not in spans:
                    spans.append(span)

        return spans

    def dict(self, **kwargs):
        # TODO: Add **kwargs to dict call
        return super().dict(exclude={'parent', 'merge_history'})

    def path_string(self):
        return '.'.join(self.full_path())

    def full_path(self):
        path = []
        if self.parent:
            path.extend(self.parent.full_path())

        if self.identifier:
            path.append(self.identifier)

        return path

    @property
    def module(self) -> 'Module':  # type: ignore # ruff # noqa
        if self.parent:
            return self.parent.root()
        return self

    @deprecated('Use module()')
    def root(self) -> 'Module':  # type: ignore # ruff # noqa
        return self.module

    def get_blocks(
        self, has_identifier: bool, include_types: Optional[List[CodeBlockType]] = None
    ) -> List['CodeBlock']:
        blocks = [self]

        for child in self.children:
            if has_identifier and not child.identifier:
                continue

            if include_types and child.type not in include_types:
                continue

            blocks.extend(child.get_indexable_blocks())
        return blocks

    def find_reference(self, ref_path: List[str]) -> Optional[Relationship]:
        for child in self.children:
            if child.type == CodeBlockType.IMPORT:
                for reference in child.relationships:
                    if (
                        reference.path[len(reference.path) - len(ref_path) :]
                        == ref_path
                    ):
                        return reference

            child_path = child.full_path()

            if child_path[len(child_path) - len(ref_path) :] == ref_path:
                if self.type == CodeBlockType.CLASS:
                    return Relationship(scope=ReferenceScope.CLASS, path=child_path)
                if self.type == CodeBlockType.MODULE:
                    return Relationship(scope=ReferenceScope.GLOBAL, path=child_path)

                return Relationship(scope=ReferenceScope.LOCAL, path=child_path)

        if self.parent:
            return self.parent.find_reference(ref_path)

        return None

    def get_all_relationships(
        self, exclude_types: List[CodeBlockType]
    ) -> List[Relationship]:
        references = []
        references.extend(self.relationships)
        for childblock in self.children:
            if not exclude_types or childblock.type not in exclude_types:
                references.extend(
                    childblock.get_all_relationships(exclude_types=exclude_types)
                )

        return references

    def is_complete(self):
        if self.type == CodeBlockType.COMMENTED_OUT_CODE:
            return False
        for child in self.children:
            if not child.is_complete():
                return False
        return True

    def find_errors(self) -> List['CodeBlock']:
        errors = []

        if self.children:
            for child in self.children:
                errors.extend(child.find_errors())

        if self.type == CodeBlockType.ERROR:
            errors.append(self)

        return errors

    def find_validation_errors(self) -> List[ValidationError]:
        errors = []
        errors.extend(self.validation_errors)

        for child in self.children:
            errors.extend(child.find_validation_errors())

        return errors

    def create_commented_out_block(self, comment_out_str: str = '...'):
        return CodeBlock(
            type=CodeBlockType.COMMENTED_OUT_CODE,
            indentation=self.indentation,
            parent=self,
            pre_lines=1,
            content=self.create_comment(comment_out_str),
        )

    def create_comment_block(self, comment: str = '...', pre_lines: int = 1):
        return CodeBlock(
            type=CodeBlockType.COMMENT,
            indentation=self.indentation,
            parent=self,
            pre_lines=pre_lines,
            content=self.create_comment(comment),
        )

    def create_comment(self, comment: str) -> str:
        symbol = get_comment_symbol('python')  # FIXME: Derive language from Module
        return f'{symbol} {comment}'

    def add_indentation(self, indentation: str):
        if self.pre_lines:
            self.indentation += indentation

        # TODO: Find a more graceful way to solve multi line blocks
        if '\n' in self.content:
            lines = self.content.split('\n')
            content = lines[0]
            for line in lines[1:]:
                if line.startswith(' '):
                    content += '\n' + indentation + line
            self.content = content

        for child in self.children:
            child.add_indentation(indentation)

    def find_by_path(self, path: List[str]) -> Optional['CodeBlock']:
        if not path:
            return self

        for child in self.children:
            if child.identifier == path[0]:
                if len(path) == 1:
                    return child
                else:
                    return child.find_by_path(path[1:])

        return None

    def find_blocks_by_span_id(self, span_id: str) -> List['CodeBlock']:
        blocks = []
        if self.belongs_to_span and self.belongs_to_span.span_id == span_id:
            blocks.append(self)

        for child in self.children:
            # TODO: Optimize to just check relevant children (by mapping spans?
            blocks.extend(child.find_blocks_by_span_id(span_id))

        return blocks

    def find_last_before_span(
        self, span_id: str, last_before_span: Optional['CodeBlock'] = None
    ) -> Optional['CodeBlock']:
        if self.belongs_to_span and self.belongs_to_span.span_id == span_id:
            return last_before_span

        for child in self.children:
            if child.belongs_to_span and child.belongs_to_span.span_id == span_id:
                return last_before_span

            if child.belongs_to_span and child.belongs_to_span.span_id != span_id:
                last_before_span = child

            result = child.find_last_before_span(span_id, last_before_span)
            if result:
                return result

        return None

    def find_first_by_span_id(self, span_id: str) -> Optional['CodeBlock']:
        if self.belongs_to_span and self.belongs_to_span.span_id == span_id:
            return self

        for child in self.children:
            found = child.find_first_by_span_id(span_id)
            if found:
                return found

        return None

    def find_last_by_span_id(self, span_id: str) -> Optional['CodeBlock']:
        for child in reversed(self.children):
            if child.belongs_to_span and child.belongs_to_span.span_id == span_id:
                return child

            found = child.find_last_by_span_id(span_id)
            if found:
                return found

        return None

    def has_any_block(self, blocks: List['CodeBlock']) -> bool:
        for block in blocks:
            if block.full_path()[: len(self.full_path())] == self.full_path():
                return True
        return False

    def find_by_identifier(
        self,
        identifier: str,
        type: Optional[CodeBlockType] = None,
        recursive: bool = False,
    ):
        for child in self.children:
            if child.identifier == identifier and (not type or child.type == type):
                return child

            if recursive:
                found = child.find_by_identifier(identifier, type, recursive)
                if found:
                    return found
        return None

    def find_blocks_with_identifier(self, identifier: str) -> List['CodeBlock']:
        blocks = []
        for child_block in self.children:
            if child_block.identifier == identifier:
                blocks.append(child_block)
            blocks.extend(child_block.find_blocks_with_identifier(identifier))
        return blocks

    def find_incomplete_blocks_with_type(self, block_type: CodeBlockType):
        return self.find_incomplete_blocks_with_types([block_type])

    def find_incomplete_blocks_with_types(self, block_types: List[CodeBlockType]):
        matching_blocks = []
        for child_block in self.children:
            if child_block.type in block_types and not child_block.is_complete():
                matching_blocks.append(child_block)

            if child_block.children:
                matching_blocks.extend(
                    child_block.find_incomplete_blocks_with_types(block_types)
                )

        return matching_blocks

    def find_blocks_with_types(
        self, block_types: List[CodeBlockType]
    ) -> List['CodeBlock']:
        matching_blocks = []
        if self.type in block_types:
            matching_blocks.append(self)
        for child_block in self.children:
            matching_blocks.extend(
                child_block.find_blocks_with_types(block_types=block_types)
            )
        return matching_blocks

    def has_blocks_with_types(self, block_types: List[CodeBlockType]) -> bool:
        if self.type in block_types:
            return True
        for child_block in self.children:
            if child_block.has_blocks_with_types(block_types):
                return True
        return False

    def find_blocks_with_type(self, block_type: CodeBlockType) -> List['CodeBlock']:
        return self.find_blocks_with_types([block_type])

    def find_first_by_start_line(self, start_line: int) -> Optional['CodeBlock']:
        for child in self.children:
            if child.start_line >= start_line:
                return child

            if child.end_line >= start_line:
                if not child.children:
                    return child

                found = child.find_first_by_start_line(start_line)
                if found:
                    return found

        return None

    def find_last_by_end_line(
        self, end_line: int, tokens: Optional[int] = None
    ) -> Optional['CodeBlock']:
        last_child = None
        for child in self.children:
            if child.start_line > end_line or (tokens and child.tokens > tokens):
                return last_child

            if tokens:
                tokens -= child.tokens

            last_child = child

            if child.end_line > end_line:
                found = child.find_last_by_end_line(end_line, tokens=tokens)
                if found:
                    return found

        return None

    def find_closest_indexed_parent(self) -> Optional['CodeBlock']:
        if self.is_indexed:
            return self

        if self.parent:
            return self.parent.find_closest_indexed_parent()

        return None

    def find_indexed_blocks(self):
        indexed_blocks = []
        for child in self.children:
            if child.is_indexed:
                indexed_blocks.append(child)
            indexed_blocks.extend(child.find_indexed_blocks())
        return indexed_blocks

    def get_indexed_blocks(self) -> List['CodeBlock']:
        blocks = []
        for child in self.children:
            if child.is_indexed:
                blocks.append(child)

            blocks.extend(child.get_indexed_blocks())

        return blocks

    def line_witin_token_context(self, line_number: int, tokens: int) -> bool:
        if tokens <= 0:
            return False

        if self.end_line < line_number:
            if not self.next:
                return False
            if self.next.start_line > line_number:
                return True
            else:
                return self.next.line_witin_token_context(
                    line_number, tokens - self.tokens
                )
        else:
            if not self.previous:
                return False
            elif self.previous.end_line < line_number:
                return True
            else:
                return self.previous.line_witin_token_context(
                    line_number, tokens - self.tokens
                )

    def tokens_from_line(self, line_number: int) -> Optional[int]:
        if not self.previous or self.previous.end_line < line_number:
            return self.tokens

        return self.tokens + (self.previous.tokens_from_line(line_number) or 0)

    def last_block_until_line(self, line_number: int, tokens: int) -> 'CodeBlock':
        if self.end_line < line_number:
            if (
                not self.next
                or self.next.start_line > line_number
                or self.next.tokens > tokens
            ):
                return self
            else:
                return self.next.last_block_until_line(
                    line_number, tokens - self.tokens
                )
        else:
            if (
                not self.previous
                or self.previous.end_line < line_number
                or (self.next and self.next.tokens > tokens)
            ):
                return self
            else:
                return self.previous.last_block_until_line(
                    line_number, tokens - self.tokens
                )

    def get_all_span_ids(self, include_self: bool = True) -> Set[str]:
        span_ids = set()

        if include_self and self.belongs_to_span:
            span_ids.add(self.belongs_to_span.span_id)

        for child in self.children:
            span_ids.update(child.get_all_span_ids())

        return span_ids

    def has_span(self, span_id: str):
        return self.has_any_span({span_id})

    def has_any_span(self, span_ids: Set[str]):
        all_span_ids = self.get_all_span_ids(include_self=False)
        return any([span_id in all_span_ids for span_id in span_ids])

    def belongs_to_any_span(self, span_ids: Set[str]):
        return self.belongs_to_span and self.belongs_to_span.span_id in span_ids

    def has_lines(self, start_line: int, end_line: int):
        # Returns True if any part of the block is within the provided line range
        return not (self.end_line < start_line or self.start_line > end_line)

    def is_within_lines(self, start_line: int, end_line: int):
        return self.start_line >= start_line and self.end_line <= end_line

    def has_content(self, query: str, span_id: Optional[str] = None):
        if (
            self.content
            and query in self.content
            and (
                not span_id
                or (self.belongs_to_span and self.belongs_to_span.span_id == span_id)
            )
        ):
            return True

        if span_id and not self.has_span(span_id):
            return False

        for child in self.children:
            if child.has_content(query, span_id):
                return True

        return False
