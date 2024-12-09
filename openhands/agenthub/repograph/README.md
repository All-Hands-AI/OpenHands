# RepoGraph for OpenHands

This module provides repository-level code graph analysis capabilities for OpenHands. It is adapted from [RepoGraph](https://github.com/ozyyshr/RepoGraph) and integrated into the OpenHands ecosystem.

## Features

- Repository-level code analysis
- Function and class dependency tracking
- Graph-based code navigation
- Search capabilities (DFS, BFS, neighbor analysis)

## Usage

```python
from openhands.agenthub.repograph import RepoGraphAnalyzer, GraphSearcher

# Initialize analyzer
analyzer = RepoGraphAnalyzer(root="/path/to/repo", verbose=True)

# Analyze specific files
files = ["/path/to/repo/file1.py", "/path/to/repo/file2.py"]
tags, graph = analyzer.analyze(files)

# Initialize searcher
searcher = GraphSearcher(graph)

# Find neighbors of a function/class
neighbors = searcher.one_hop_neighbors("MyClass")

# Perform depth-first search
dfs_results = searcher.dfs("MyFunction", depth=3)

# Perform breadth-first search
bfs_results = searcher.bfs("MyFunction", depth=3)
```

See `example.py` for a complete usage example.

## Components

- `graph.py`: Core graph analysis functionality
- `searcher.py`: Graph search capabilities
- `utils.py`: Utility functions for code parsing
- `example.py`: Example usage and demonstration

## Credits

This module is adapted from the [RepoGraph](https://github.com/ozyyshr/RepoGraph) project. The original implementation has been modified and enhanced to integrate with OpenHands.