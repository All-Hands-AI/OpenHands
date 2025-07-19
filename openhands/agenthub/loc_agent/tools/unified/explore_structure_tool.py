"""ExploreStructureTool for traversing code graph to retrieve dependency structure."""

from typing import Any, Dict, List, Optional, Union

from litellm import ChatCompletionToolParam

from openhands.agenthub.codeact_agent.tools.unified.base import Tool, ToolValidationError


class ExploreStructureTool(Tool):
    """Tool for exploring repository structure and code dependencies.
    
    Traverses a pre-built code graph to retrieve dependency structure around specified entities,
    with options to explore upstream or downstream, and control traversal depth and filters.
    """
    
    def __init__(self, use_simplified_description: bool = False):
        super().__init__(
            name="explore_tree_structure",
            description="Traverses a pre-built code graph to retrieve dependency structure around specified entities"
        )
        self.use_simplified_description = use_simplified_description
    
    def get_schema(self, use_short_description: bool = False) -> ChatCompletionToolParam:
        """Get the tool schema for function calling."""
        if self.use_simplified_description or use_short_description:
            description = """
A unified tool that traverses a pre-built code graph to retrieve dependency structure around specified entities,
with options to explore upstream or downstream, and control traversal depth and filters for entity and dependency types.
"""
            example = """
Example Usage:
1. Exploring Downstream Dependencies:
    ```
    explore_tree_structure(
        start_entities=['src/module_a.py:ClassA'],
        direction='downstream',
        traversal_depth=2,
        dependency_type_filter=['invokes', 'imports']
    )
    ```
2. Exploring the repository structure from the root directory (/) up to two levels deep:
    ```
    explore_tree_structure(
      start_entities=['/'],
      traversal_depth=2,
      dependency_type_filter=['contains']
    )
    ```
3. Generate Class Diagrams:
    ```
    explore_tree_structure(
        start_entities=selected_entity_ids,
        direction='both',
        traverse_depth=-1,
        dependency_type_filter=['inherits']
    )
    ```
"""
        else:
            description = """
Unified repository exploring tool that traverses a pre-built code graph to retrieve dependency structure around specified entities.
The search can be controlled to traverse upstream (exploring dependencies that entities rely on) or downstream (exploring how entities impact others), with optional limits on traversal depth and filters for entity and dependency types.

Code Graph Definition:
* Entity Types: 'directory', 'file', 'class', 'function'.
* Dependency Types: 'contains', 'imports', 'invokes', 'inherits'.
* Hierarchy:
    - Directories contain files and subdirectories.
    - Files contain classes and functions.
    - Classes contain inner classes and methods.
    - Functions can contain inner functions.
* Interactions:
    - Files/classes/functions can import classes and functions.
    - Classes can inherit from other classes.
    - Classes and functions can invoke others (invocations in a class's `__init__` are attributed to the class).
Entity ID:
* Unique identifier including file path and module path.
* Here's an example of an Entity ID: `"interface/C.py:C.method_a.inner_func"` identifies function `inner_func` within `method_a` of class `C` in `"interface/C.py"`.

Notes:
* Traversal Control: The `traversal_depth` parameter specifies how deep the function should explore the graph starting from the input entities.
* Filtering: Use `entity_type_filter` and `dependency_type_filter` to narrow down the scope of the search, focusing on specific entity types and relationships.
"""
            example = """
Example Usage:
1. Exploring Outward Dependencies:
    ```
    explore_tree_structure(
        start_entities=['src/module_a.py:ClassA'],
        direction='downstream',
        traversal_depth=2,
        dependency_type_filter=['invokes', 'imports']
    )
    ```
    This retrieves the dependencies of `ClassA` up to 2 levels deep, focusing only on classes and functions with 'invokes' and 'imports' relationships.

2. Exploring Inward Dependencies:
    ```
    explore_tree_structure(
        start_entities=['src/module_b.py:FunctionY'],
        direction='upstream',
        traversal_depth=-1
    )
    ```
    This finds all entities that depend on `FunctionY` without restricting the traversal depth.
3. Exploring Repository Structure:
    ```
    explore_tree_structure(
      start_entities=['/'],
      traversal_depth=2,
      dependency_type_filter=['contains']
    )
    ```
    This retrieves the tree repository structure from the root directory (/), traversing up to two levels deep and focusing only on 'contains' relationship.
4. Generate Class Diagrams:
    ```
    explore_tree_structure(
        start_entities=selected_entity_ids,
        direction='both',
        traverse_depth=-1,
        dependency_type_filter=['inherits']
    )
    ```
"""
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (description + example).strip(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_entities": {
                            "description": (
                                "List of entities (e.g., class, function, file, or directory paths) to begin the search from.\n"
                                "Entities representing classes or functions must be formatted as \"file_path:QualifiedName\" (e.g., `interface/C.py:C.method_a.inner_func`).\n"
                                "For files or directories, provide only the file or directory path (e.g., `src/module_a.py` or `src/`)."
                            ),
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "direction": {
                            "description": (
                                "Direction of traversal in the code graph; allowed options are: `upstream`, `downstream`, `both`.\n"
                                "- 'upstream': Traversal to explore dependencies that the specified entities rely on (how they depend on others).\n"
                                "- 'downstream': Traversal to explore the effects or interactions of the specified entities on others (how others depend on them).\n"
                                "- 'both': Traversal on both direction."
                            ),
                            "type": "string",
                            "enum": ["upstream", "downstream", "both"],
                            "default": "downstream",
                        },
                        "traversal_depth": {
                            "description": (
                                "Maximum depth of traversal. A value of -1 indicates unlimited depth (subject to a maximum limit)."
                                "Must be either `-1` or a non-negative integer (≥ 0)."
                            ),
                            "type": "integer",
                            "default": 2,
                        },
                        "entity_type_filter": {
                            "description": (
                                "List of entity types (e.g., 'class', 'function', 'file', 'directory') to include in the traversal. If None, all entity types are included."
                            ),
                            "type": ["array", "null"],
                            "items": {"type": "string"},
                            "default": None,
                        },
                        "dependency_type_filter": {
                            "description": (
                                "List of dependency types (e.g., 'contains', 'imports', 'invokes', 'inherits') to include in the traversal. If None, all dependency types are included."
                            ),
                            "type": ["array", "null"],
                            "items": {"type": "string"},
                            "default": None,
                        },
                    },
                    "required": ["start_entities"],
                },
            },
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize tool parameters."""
        if "start_entities" not in parameters:
            raise ToolValidationError("Missing required parameter 'start_entities'")
        
        start_entities = parameters["start_entities"]
        direction = parameters.get("direction", "downstream")
        traversal_depth = parameters.get("traversal_depth", 2)
        entity_type_filter = parameters.get("entity_type_filter")
        dependency_type_filter = parameters.get("dependency_type_filter")
        
        # Validate start_entities
        if not isinstance(start_entities, list):
            raise ToolValidationError("Parameter 'start_entities' must be a list")
        
        if not start_entities:
            raise ToolValidationError("Parameter 'start_entities' cannot be empty")
        
        for i, entity in enumerate(start_entities):
            if not isinstance(entity, str):
                raise ToolValidationError(f"Entity at index {i} must be a string")
            if not entity.strip():
                raise ToolValidationError(f"Entity at index {i} cannot be empty")
        
        # Validate direction
        valid_directions = ["upstream", "downstream", "both"]
        if direction not in valid_directions:
            raise ToolValidationError(f"Parameter 'direction' must be one of {valid_directions}")
        
        # Validate traversal_depth
        if not isinstance(traversal_depth, int):
            raise ToolValidationError("Parameter 'traversal_depth' must be an integer")
        
        if traversal_depth != -1 and traversal_depth < 0:
            raise ToolValidationError("Parameter 'traversal_depth' must be -1 or non-negative")
        
        # Validate entity_type_filter
        if entity_type_filter is not None:
            if not isinstance(entity_type_filter, list):
                raise ToolValidationError("Parameter 'entity_type_filter' must be a list or null")
            
            valid_entity_types = ["directory", "file", "class", "function"]
            for i, entity_type in enumerate(entity_type_filter):
                if not isinstance(entity_type, str):
                    raise ToolValidationError(f"Entity type at index {i} must be a string")
                if entity_type not in valid_entity_types:
                    raise ToolValidationError(f"Entity type '{entity_type}' is not valid. Must be one of {valid_entity_types}")
        
        # Validate dependency_type_filter
        if dependency_type_filter is not None:
            if not isinstance(dependency_type_filter, list):
                raise ToolValidationError("Parameter 'dependency_type_filter' must be a list or null")
            
            valid_dependency_types = ["contains", "imports", "invokes", "inherits"]
            for i, dep_type in enumerate(dependency_type_filter):
                if not isinstance(dep_type, str):
                    raise ToolValidationError(f"Dependency type at index {i} must be a string")
                if dep_type not in valid_dependency_types:
                    raise ToolValidationError(f"Dependency type '{dep_type}' is not valid. Must be one of {valid_dependency_types}")
        
        # Normalize parameters
        result = {
            "start_entities": [entity.strip() for entity in start_entities],
            "direction": direction,
            "traversal_depth": traversal_depth,
        }
        
        if entity_type_filter is not None:
            result["entity_type_filter"] = entity_type_filter
        
        if dependency_type_filter is not None:
            result["dependency_type_filter"] = dependency_type_filter
        
        return result