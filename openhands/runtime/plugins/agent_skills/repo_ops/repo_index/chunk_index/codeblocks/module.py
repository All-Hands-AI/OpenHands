# import logging
from typing import Dict, Optional, Set

from networkx import DiGraph
from pydantic import (
    ConfigDict,
)
from openhands.runtime.plugins.agent_skills.repo_ops.repo_index.chunk_index.codeblocks.codeblocks import (
    BlockSpan,
    CodeBlock,
    CodeBlockType,
    SpanType,
)

# logger = logging.getLogger(__name__)


class Module(CodeBlock):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: str
    content: str
    spans_by_id: Dict[str, BlockSpan] = {}
    language: str | None = None
    parent: CodeBlock | None = None

    _graph: DiGraph = None  # TODO: Move to central CodeGraph

    def __init__(self, **data):
        data.setdefault('type', CodeBlockType.MODULE)
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
            if (
                block.parent
                and block.parent.type == CodeBlockType.CLASS
                and block.belongs_to_span is not None
            ):
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
