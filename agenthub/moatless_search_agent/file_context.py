import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel

from .codeblocks import CodeBlockType
from .codeblocks.codeblocks import (
    BlockSpan,
    CodeBlock,
    CodeBlockTypeGroup,
    SpanMarker,
    SpanType,
)
from .repository import CodeFile, FileRepository, UpdateResult
from .settings import Settings
from .types import FileWithSpans

logger = logging.getLogger(__name__)


@dataclass
class RankedFileSpan:
    file_path: str
    span_id: str
    rank: int


class ContextSpan(BaseModel):
    span: BlockSpan
    tokens: Optional[int] = None

    @property
    def span_id(self):
        return self.span.span_id

    def dict(self, **kwargs):
        return self.model_dump(**kwargs)

    def model_dump(self, **kwargs):
        return {'span_id': self.span_id, 'tokens': self.tokens}


@dataclass
class CurrentPromptSpan:
    span_id: Optional[str] = None
    tokens: int = 0


class ContextFile(BaseModel):
    file: CodeFile
    spans: List[ContextSpan] = []

    def __init__(self, **data):
        super().__init__(**data)

    @property
    def file_path(self):
        return self.file.file_path

    @property
    def module(self):
        return self.file.module

    @property
    def content(self):
        return self.file.content

    @property
    def span_ids(self):
        return {span.span_id for span in self.spans}

    def to_prompt(
        self,
        show_span_ids=False,
        show_line_numbers=False,
        exclude_comments=False,
        show_outcommented_code=False,
        outcomment_code_comment: str = '...',
    ):
        if self.span_ids is not None and len(self.span_ids) == 0:
            logger.warning(f'No span ids provided for {self.file_path}, return empty')
            return ''

        code = self._to_prompt(
            code_block=self.module,
            show_span_id=show_span_ids,
            show_line_numbers=show_line_numbers,
            outcomment_code_comment=outcomment_code_comment,
            show_outcommented_code=show_outcommented_code,
            exclude_comments=exclude_comments,
        )

        return f'**{self.file_path}**\n```\n{code}\n```\n\n'

    def _find_span(self, codeblock: CodeBlock) -> Optional[ContextSpan]:
        if not codeblock.belongs_to_span:
            return None

        for span in self.spans:
            if codeblock.belongs_to_span.span_id == span.span_id:
                return span

        return None

    def _to_prompt(
        self,
        code_block: CodeBlock,
        current_span: Optional[CurrentPromptSpan] = None,
        show_outcommented_code: bool = True,
        outcomment_code_comment: str = '...',
        show_span_id: bool = False,
        show_line_numbers: bool = False,
        exclude_comments: bool = False,
    ):
        if not current_span:
            current_span = CurrentPromptSpan()

        contents = ''

        outcommented_block = None
        for i, child in enumerate(code_block.children):
            if exclude_comments and child.type.group == CodeBlockTypeGroup.COMMENT:
                continue

            show_new_span_id = False
            show_child = False
            child_span = self._find_span(child)

            if child_span:
                if child_span.span_id != current_span.span_id:
                    show_child = True
                    show_new_span_id = show_span_id
                    current_span = CurrentPromptSpan(child_span.span_id)
                elif not child_span.tokens:
                    show_child = True
                else:
                    # Count all tokens in child block if it's not a structure (function or class) or a 'compound' (like an 'if' or 'for' clause)
                    if (
                        child.type.group == CodeBlockTypeGroup.IMPLEMENTATION
                        and child.type
                        not in [CodeBlockType.COMPOUND, CodeBlockType.DEPENDENT_CLAUSE]
                    ):
                        child_tokens = child.sum_tokens()
                    else:
                        child_tokens = child.tokens

                    if current_span.tokens + child_tokens <= child_span.tokens:
                        show_child = True

                    current_span.tokens += child_tokens

            elif (
                not child.belongs_to_span or child.belongs_to_any_span not in self.spans
            ) and child.has_any_span(self.span_ids):
                show_child = True

                if (
                    child.belongs_to_span
                    and current_span.span_id != child.belongs_to_span.span_id
                ):
                    show_new_span_id = show_span_id
                    current_span = CurrentPromptSpan(child.belongs_to_span.span_id)

            if show_child:
                # if outcommented_block:
                #     contents += outcommented_block._to_prompt_string(
                #         show_line_numbers=show_line_numbers
                #     )

                outcommented_block = None

                contents += child._to_prompt_string(
                    show_span_id=show_new_span_id,
                    show_line_numbers=show_line_numbers,
                    span_marker=SpanMarker.TAG,
                )
                contents += self._to_prompt(
                    code_block=child,
                    exclude_comments=exclude_comments,
                    show_outcommented_code=show_outcommented_code,
                    outcomment_code_comment=outcomment_code_comment,
                    show_span_id=show_span_id,
                    current_span=current_span,
                    show_line_numbers=show_line_numbers,
                )
            elif show_outcommented_code and not outcommented_block:
                outcommented_block = child.create_commented_out_block(
                    outcomment_code_comment
                )
                outcommented_block.start_line = child.start_line

        if (
            outcomment_code_comment
            and outcommented_block
            and child.type
            not in [
                CodeBlockType.COMMENT,
                CodeBlockType.COMMENTED_OUT_CODE,
                CodeBlockType.SPACE,
            ]
        ):
            contents += outcommented_block._to_prompt_string(
                show_line_numbers=show_line_numbers
            )

        return contents

    def context_size(self):
        if self.span_ids is None:
            return self.module.sum_tokens()
        else:
            tokens = 0
            for span_id in self.span_ids:
                span = self.module.find_span_by_id(span_id)
                if span:
                    tokens += span.tokens
            return tokens

    def add_spans(
        self,
        span_ids: Set[str],
        tokens: Optional[int] = None,
    ):
        for span_id in span_ids:
            self.add_span(span_id, tokens)

    def add_span(
        self,
        span_id: str,
        tokens: Optional[int] = None,
    ):
        existing_span = next(
            (span for span in self.spans if span.span_id == span_id), None
        )

        if existing_span:
            existing_span.tokens = tokens
        else:
            span = self.module.find_span_by_id(span_id)
            if span:
                self.spans.append(ContextSpan(span=span, tokens=tokens))
            else:
                logger.warning(
                    f'Could not find span with id {span_id} in file {self.file_path}'
                )

    def remove_span(self, span_id: str):
        self.spans = [span for span in self.spans if span.span_id != span_id]

    def get_spans(self) -> List[BlockSpan]:
        return [span.span for span in self.spans]

    def get_span(self, span_id: str) -> Optional[BlockSpan]:
        for span in self.spans:
            if span.span_id == span_id:
                return span.span
        return None

    def update_content_by_line_numbers(
        self, start_line_index: int, end_line_index: int, replacement_content: str
    ) -> UpdateResult:
        update_result = self.file.update_content_by_line_numbers(
            start_line_index, end_line_index, replacement_content
        )

        if update_result.new_span_ids:
            self.add_spans(update_result.new_span_ids)

        return update_result

    def expand_context_with_imports(self):
        init_spans = set()
        for child in self.module.children:
            if (
                child.type == CodeBlockType.IMPORT
                and child.belongs_to_span.span_type == SpanType.INITATION
                and child.belongs_to_span.span_id not in init_spans
            ):
                self.add_span(child.belongs_to_span.span_id)

    def expand_small_classes(self, max_tokens: int):
        """
        Expand small classes with no other spans selected if the context allows it.

        TODO: This a temporary solution, should be handled by asking the LLM to specify spans in the Identify step.
        """

        if len(self.spans) == 1:
            span = self.module.find_span_by_id(self.spans[0].span_id)
            if (
                span
                and span.initiating_block.type == CodeBlockType.CLASS
                and span.initiating_block.sum_tokens() < max_tokens
            ):
                for span_id in span.initiating_block.get_all_span_ids():
                    self.add_span(span_id)


class FileContext:
    def __init__(self, repo: FileRepository, max_tokens: int = 4000):
        self._repo = repo
        self._file_context: Dict[str, ContextFile] = {}
        self._max_tokens: int = max_tokens

    @classmethod
    def from_json(cls, repo_path: str, context_data: list[Dict]):
        file_context = cls(FileRepository(repo_path))

        for file_data in context_data:
            file_context.add_spans_to_context(
                file_path=file_data['file_path'], span_ids=set(file_data['span_ids'])
            )

        return file_context

    def to_files_with_spans(self) -> List[FileWithSpans]:
        return [
            FileWithSpans(file_path=file_path, span_ids=list(file.span_ids))
            for file_path, file in self._file_context.items()
        ]

    def add_files_with_spans(self, files_with_spans: List[FileWithSpans]):
        for file_with_spans in files_with_spans:
            self.add_spans_to_context(
                file_with_spans.file_path, set(file_with_spans.span_ids)
            )

    def remove_file(self, file_path: str):
        if file_path in self._file_context:
            if file_path in self._file_context:
                del self._file_context[file_path]

    def exists(self, file_path: str):
        return file_path in self._file_context

    @property
    def files(self):
        return list(self._file_context.values())

    def get_file(self, file_path: str) -> Optional[ContextFile]:
        return self._file_context.get(file_path)

    def add_spans_to_context(
        self,
        file_path: str,
        span_ids: Set[str],
        tokens: Optional[int] = None,
    ):
        context_file = self.get_context_file(file_path)
        if context_file:
            context_file.add_spans(span_ids, tokens)
        else:
            logger.warning(f'Could not find file {file_path} in the repository')

    def add_span_to_context(
        self, file_path: str, span_id: str, tokens: Optional[int] = None
    ):
        context_file = self.get_context_file(file_path)
        if context_file:
            context_file.add_span(span_id, tokens)

    def remove_span_from_context(
        self, file_path: str, span_id: str, remove_file: bool = False
    ):
        context_file = self.get_context_file(file_path)
        if context_file:
            context_file.remove_span(span_id)

            if not context_file.spans and remove_file:
                self.remove_file(file_path)

    def remove_spans_from_context(
        self, file_path: str, span_ids: list[str], remove_file: bool = False
    ):
        for span_id in span_ids:
            self.remove_span_from_context(file_path, span_id, remove_file)

    def get_spans(self, file_path: str) -> List[BlockSpan]:
        context_file = self.get_context_file(file_path)
        if context_file:
            return context_file.get_spans()
        return []

    def get_span(self, file_path: str, span_id: str) -> Optional[BlockSpan]:
        context_file = self.get_context_file(file_path)
        if context_file:
            return context_file.get_span(span_id)
        return None

    def has_span(self, file_path: str, span_id: str):
        context_file = self.get_context_file(file_path)
        if context_file:
            return span_id in context_file.span_ids
        return False

    def add_ranked_spans(
        self,
        ranked_spans: List[RankedFileSpan],
        decay_rate: float = 1.2,
        min_tokens: int = 10,
    ):
        if not ranked_spans:
            logger.info('No ranked spans provided')
            return

        ranked_spans.sort(key=lambda x: x.rank)

        num_spans = len(ranked_spans)
        base_tokens_needed = num_spans * min_tokens

        # Filter out the lowest ranking spans if necessary
        while base_tokens_needed > self._max_tokens and ranked_spans:
            ranked_spans.pop()  # Remove the span with the lowest rank
            num_spans = len(ranked_spans)
            base_tokens_needed = num_spans * min_tokens

        if not ranked_spans:
            raise ValueError(
                'Not enough tokens to meet the minimum token requirement for any span'
            )

        remaining_tokens = self._max_tokens - base_tokens_needed

        # Calculate total weights using exponential decay
        total_weight = sum([decay_rate ** (-span.rank) for span in ranked_spans])

        # Assign tokens based on the weight
        tokens_distribution = []
        for span in ranked_spans:
            weight = decay_rate ** (-span.rank)
            allocated_tokens = min_tokens + int(
                remaining_tokens * (weight / total_weight)
            )
            tokens_distribution.append((span, allocated_tokens))

        # Adjust tokens for spans with the same rank
        rank_groups: Any = {}
        for span, tokens in tokens_distribution:
            if span.rank not in rank_groups:
                rank_groups[span.rank] = []
            rank_groups[span.rank].append((span, tokens))

        final_tokens_distribution = []
        for rank, group in rank_groups.items():
            total_tokens_for_rank = sum(tokens for _, tokens in group)
            equal_tokens = total_tokens_for_rank // len(group)
            for span, _ in group:
                final_tokens_distribution.append((span, equal_tokens))

        # Distribute tokens and add spans to the context
        sum_tokens = 0
        for span, tokens in final_tokens_distribution:
            self.add_span_to_context(span.file_path, span.span_id, tokens)
            sum_tokens += tokens

        logger.info(
            f'Added {len(final_tokens_distribution)} spans with {sum_tokens} tokens'
        )

    def expand_context_with_imports(self):
        for file in self._file_context.values():
            file.expand_context_with_imports()

    def expand_small_classes(self, max_tokens: int):
        for file in self._file_context.values():
            file.expand_small_classes(max_tokens)

    def expand_context_with_related_spans(
        self, max_tokens: int = Settings.max_context_tokens
    ):
        spans = 0

        # Add related spans if context allows it
        if self.context_size() > max_tokens:
            return spans

        for file in self._file_context.values():
            if not file.span_ids:
                continue
            current_span_ids = list(file.span_ids)
            for span_id in current_span_ids:
                related_span_ids = file.module.find_related_span_ids(span_id)

                for related_span_id in related_span_ids:
                    if related_span_id in file.span_ids:
                        continue

                    related_span = file.module.find_span_by_id(related_span_id)
                    if related_span.tokens + self.context_size() > max_tokens:
                        return spans

                    spans += 1
                    file.add_span(related_span_id)

        return spans

    def get_context_file(self, file_path: str) -> Optional[ContextFile]:
        if file_path not in self._file_context:
            file = self._repo.get_file(file_path)
            if not file:
                return None
            self._file_context[file_path] = ContextFile(
                file=self._repo.get_file(file_path), span_ids=set()
            )

        return self._file_context[file_path]

    def context_size(self):
        return sum(file.context_size() for file in self._file_context.values())

    def save_file(self, file_path: str, updated_content: Optional[str] = None):
        self._repo.save_file(file_path, updated_content)

    def save(self):
        self._repo.save()

    def dict(self):
        file_dict = []
        for file_path, file in self._file_context.items():
            if file.spans:
                spans = []
                for span in file.spans:
                    spans.append({'span_id': span.span_id, 'tokens': span.tokens})
                file_dict.append({'file_path': file_path, 'spans': spans})
            else:
                file_dict.append({'file_path': file_path})
        return file_dict

    def reset(self):
        self._file_context = {}

    def create_prompt(
        self,
        show_span_ids=False,
        show_line_numbers=True,
        exclude_comments=False,
        show_outcommented_code=False,
        outcomment_code_comment: str = '...',
    ):
        file_context_content = ''
        for file in self._file_context.values():
            content = file.to_prompt(
                show_span_ids,
                show_line_numbers,
                exclude_comments,
                show_outcommented_code,
                outcomment_code_comment,
            )
            file_context_content += '\n\n' + content
        return file_context_content
