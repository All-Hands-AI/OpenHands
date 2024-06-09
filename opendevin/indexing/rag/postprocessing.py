from typing import List, Optional

from llama_index.core.schema import NodeWithScore, QueryBundle

# TODO: define custom node postprocessors here


class DeduplicateNodePostprocessor:
    def postprocess_nodes(
        self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle]
    ) -> List[NodeWithScore]:
        """Postprocess nodes."""
        print('Postprocessing nodes entered')

        unique_hashes = set()
        unique_nodes = []

        for node in nodes:
            node_hash = node.node.hash

            if node_hash not in unique_hashes:
                unique_hashes.add(node_hash)
                unique_nodes.append(node)

        return unique_nodes
