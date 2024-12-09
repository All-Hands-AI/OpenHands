"""Example usage of RepoGraph in OpenHands."""

import os
from pathlib import Path
from typing import List, Dict, Any
import networkx as nx
from .graph import RepoGraphAnalyzer
from .searcher import GraphSearcher

def analyze_repository(repo_path: str, files: List[str] = None) -> Dict[str, Any]:
    """Analyze a repository using RepoGraph.
    
    Args:
        repo_path: Path to the repository
        files: Optional list of specific files to analyze. If None, analyzes all Python files.
        
    Returns:
        Dictionary containing analysis results
    """
    # Initialize analyzer
    analyzer = RepoGraphAnalyzer(root=repo_path, verbose=True)
    
    # Get files to analyze
    if files is None:
        files = []
        for root, _, filenames in os.walk(repo_path):
            for filename in filenames:
                if filename.endswith('.py'):
                    files.append(os.path.join(root, filename))
    
    # Analyze repository
    tags, graph = analyzer.analyze(files)
    
    # Initialize searcher
    searcher = GraphSearcher(graph)
    
    # Example analysis
    results = {
        'files_analyzed': len(files),
        'total_nodes': len(graph.nodes),
        'total_edges': len(graph.edges),
        'node_types': {},
        'most_connected': [],
    }
    
    # Count node types
    for node, attrs in graph.nodes(data=True):
        category = attrs.get('category', 'unknown')
        results['node_types'][category] = results['node_types'].get(category, 0) + 1
    
    # Find most connected nodes
    degree_centrality = nx.degree_centrality(graph)
    most_connected = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    results['most_connected'] = [
        {
            'name': node,
            'centrality': round(centrality, 3),
            'neighbors': searcher.one_hop_neighbors(node)
        }
        for node, centrality in most_connected
    ]
    
    return results

def main():
    """Run example analysis on the OpenHands repository."""
    repo_path = str(Path(__file__).parent.parent.parent.parent)
    results = analyze_repository(repo_path)
    
    print("\nRepository Analysis Results:")
    print("-" * 30)
    print(f"Files analyzed: {results['files_analyzed']}")
    print(f"Total nodes: {results['total_nodes']}")
    print(f"Total edges: {results['total_edges']}")
    
    print("\nNode Types:")
    for category, count in results['node_types'].items():
        print(f"  {category}: {count}")
    
    print("\nMost Connected Components:")
    for node in results['most_connected']:
        print(f"\n  {node['name']}:")
        print(f"    Centrality: {node['centrality']}")
        print(f"    Direct neighbors: {len(node['neighbors'])}")

if __name__ == '__main__':
    main()