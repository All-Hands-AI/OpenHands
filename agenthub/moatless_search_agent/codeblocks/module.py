import logging
from typing import Dict, List, Optional, Set

from networkx import DiGraph
from pydantic import (
    ConfigDict,
)

from .codeblocks import BlockSpan, CodeBlock, CodeBlockType, SpanType

logger = logging.getLogger(__name__)


class Module(CodeBlock):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Optional[str] = None
    type: CodeBlockType = CodeBlockType.MODULE
    content: str = ''
    spans_by_id: Dict[str, BlockSpan] = {}
    language: Optional[str] = None
    parent: Optional[CodeBlock] = None

    _graph: DiGraph = None  # TODO: Move to central CodeGraph

    def __init__(self, **data):
        super().__init__(**data)

    def find_span_by_id(self, span_id: str) -> Optional[BlockSpan]:
        return self.spans_by_id.get(span_id)

    def sum_tokens(self, span_ids: Optional[Set[str]] = None):
        tokens = self.tokens
        if span_ids:
            for span_id in span_ids:
                span = self.spans_by_id.get(span_id)
                if span:
                    tokens += span.tokens
            return tokens

        tokens += sum([child.sum_tokens() for child in self.children])
        return tokens

    def show_spans(
        self,
        span_ids: List[str],
        show_related: bool = False,
        max_tokens: int = 2000,
    ) -> bool:
        for span in self.spans_by_id.values():
            span.visible = False

        checked_span_ids = set()
        span_ids_to_check = []

        tokens = 0
        for span_id in span_ids:
            span = self.spans_by_id.get(span_id)  # type: ignore
            if not span:
                return False

            tokens += span.tokens
            checked_span_ids.add(span_id)
            span_ids_to_check.append(span_id)
            span.visible = True

        if not show_related:
            return True

        # Add imports from module
        for span in self.spans.values():
            if (
                span.span_type == SpanType.INITATION
                and span.span_id not in checked_span_ids
            ):
                span_ids_to_check.append(span.span_id)

        while span_ids_to_check:
            span_id = span_ids_to_check.pop(0)
            related_spans = self.find_related_spans(span_id)

            print(f'Related spans: {len(related_spans)} for {span_id}')

            # TODO: Go through priotiized related spans to make sure that the most relevant are added first
            # TODO: Verify span token size
            for span in related_spans:
                if span.tokens + tokens > max_tokens:
                    print(
                        f'Max tokens reached: {span.tokens} + {tokens} > {max_tokens}'
                    )
                    return True

                span.visible = True
                tokens += span.tokens

                if span.span_id not in checked_span_ids:
                    checked_span_ids.add(span.span_id)
                    span_ids_to_check.append(span.span_id)

        print(f'Max tokens reached {tokens} < {max_tokens}')

        return True

    def find_related_span_ids(self, span_id: str) -> Set[str]:
        related_span_ids = set()

        blocks = self.find_blocks_by_span_id(span_id)
        for block in blocks:
            # Find successors (outgoing relationships)
            successors = list(self._graph.successors(block.path_string()))
            for succ in successors:
                node_data = self._graph.nodes[succ]
                if 'block' in node_data:
                    span = node_data['block'].belongs_to_span
                    related_span_ids.add(span.span_id)

            # Find predecessors (incoming relationships)
            predecessors = list(self._graph.predecessors(block.path_string()))
            for pred in predecessors:
                node_data = self._graph.nodes[pred]
                if 'block' in node_data:
                    span = node_data['block'].belongs_to_span
                    related_span_ids.add(span.span_id)

            # Always add parent class initation span
            if block.parent and block.parent.type == CodeBlockType.CLASS:
                if block.belongs_to_span:
                    related_span_ids.add(block.belongs_to_span.span_id)
                for class_child in block.parent.children:
                    if (
                        class_child.belongs_to_span
                        and class_child.belongs_to_span.span_type == SpanType.INITATION
                    ):
                        related_span_ids.add(class_child.belongs_to_span.span_id)

        # Always add module initation span
        for span in self.spans_by_id.values():
            if (
                span.block_type == CodeBlockType.MODULE
                and span.span_type == SpanType.INITATION
            ):
                related_span_ids.add(span.span_id)

        return related_span_ids
