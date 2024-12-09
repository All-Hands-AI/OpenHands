"""
Graph search functionality for RepoGraph.
Adapted from https://github.com/ozyyshr/RepoGraph
"""

from typing import List
import networkx as nx

class GraphSearcher:
    """Search functionality for repository code graphs."""

    def __init__(self, graph: nx.MultiDiGraph):
        """Initialize the graph searcher.
        
        Args:
            graph: NetworkX graph to search
        """
        self.graph = graph

    def one_hop_neighbors(self, query: str) -> List[str]:
        """Get one-hop neighbors from the graph.
        
        Args:
            query: Node to search from
            
        Returns:
            List of neighboring node names
        """
        return list(self.graph.neighbors(query))

    def two_hop_neighbors(self, query: str) -> List[str]:
        """Get two-hop neighbors from the graph.
        
        Args:
            query: Node to search from
            
        Returns:
            List of two-hop neighbor node names
        """
        one_hop = self.one_hop_neighbors(query)
        two_hop = []
        for node in one_hop:
            two_hop.extend(self.one_hop_neighbors(node))
        return list(set(two_hop))

    def dfs(self, query: str, depth: int) -> List[str]:
        """Perform depth-first search on the graph.
        
        Args:
            query: Starting node
            depth: Maximum search depth
            
        Returns:
            List of visited node names
        """
        visited = []
        stack = [(query, 0)]
        while stack:
            node, level = stack.pop()
            if node not in visited:
                visited.append(node)
                if level < depth:
                    stack.extend(
                        [(n, level + 1) for n in self.one_hop_neighbors(node)]
                    )
        return visited
    
    def bfs(self, query: str, depth: int) -> List[str]:
        """Perform breadth-first search on the graph.
        
        Args:
            query: Starting node
            depth: Maximum search depth
            
        Returns:
            List of visited node names
        """
        visited = []
        queue = [(query, 0)]
        while queue:
            node, level = queue.pop(0)
            if node not in visited:
                visited.append(node)
                if level < depth:
                    queue.extend(
                        [(n, level + 1) for n in self.one_hop_neighbors(node)]
                    )
        return visited