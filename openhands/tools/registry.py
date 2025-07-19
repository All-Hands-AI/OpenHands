"""Tool registry for managing and accessing OpenHands tools."""

from typing import Dict, List, Optional, Type

from .base import Tool
from .bash_tool import BashTool
from .file_editor_tool import FileEditorTool


class ToolRegistry:
    """Registry for managing OpenHands tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register the default OpenHands tools."""
        self.register(BashTool())
        self.register(FileEditorTool())
    
    def register(self, tool: Tool) -> None:
        """Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """Unregister a tool from the registry.
        
        Args:
            name: Name of the tool to unregister
        """
        if name in self._tools:
            del self._tools[name]
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name.
        
        Args:
            name: Name of the tool
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, Tool]:
        """Get all registered tools.
        
        Returns:
            Dictionary mapping tool names to Tool instances
        """
        return self._tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_tool_schemas(self, use_short_description: bool = False) -> List[Dict]:
        """Get schemas for all registered tools.
        
        Args:
            use_short_description: Whether to use short descriptions
            
        Returns:
            List of tool schemas for function calling
        """
        return [tool.get_schema(use_short_description) for tool in self._tools.values()]
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered.
        
        Args:
            name: Name of the tool
            
        Returns:
            True if tool is registered, False otherwise
        """
        return name in self._tools
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
    
    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)
    
    def __iter__(self):
        """Iterate over registered tools."""
        return iter(self._tools.values())
    
    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered using 'in' operator."""
        return name in self._tools


# Global tool registry instance
default_registry = ToolRegistry()