import unittest
from typing import Dict, Any, Optional

from mcp.types import CallToolResult, Tool
from openhands.mcp.tool import BaseTool


class TestTool(BaseTool):
    """A simple test implementation of BaseTool for testing purposes."""
    
    name: str = "test_tool"
    description: str = "A test tool for unit testing"
    
    # Basic schema with primitive types
    inputSchema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "string_param": {
                "type": "string",
                "description": "A string parameter"
            },
            "integer_param": {
                "type": "integer",
                "description": "An integer parameter"
            },
            "boolean_param": {
                "type": "boolean",
                "description": "A boolean parameter"
            }
        },
        "required": ["string_param"]
    }
    
    async def execute(self, **kwargs) -> CallToolResult:
        """Test implementation of execute."""
        return CallToolResult(content=[], isError=False)


class TestNestedTool(BaseTool):
    """A test tool with nested object schemas using $ref."""
    
    name: str = "nested_tool"
    description: str = "A tool with nested schema definitions"
    
    # Schema with nested objects using $ref
    inputSchema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "user": {
                "$ref": "#/$defs/User"
            },
            "options": {
                "$ref": "#/$defs/Options"
            }
        },
        "required": ["user"],
        "$defs": {
            "User": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "User's name"
                    },
                    "age": {
                        "type": "integer",
                        "description": "User's age"
                    }
                },
                "required": ["name"],
                "description": "User information"
            },
            "Options": {
                "type": "object",
                "properties": {
                    "verbose": {
                        "type": "boolean",
                        "description": "Enable verbose output"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Result limit",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "description": "Operation options"
            }
        }
    }
    
    async def execute(self, **kwargs) -> CallToolResult:
        """Test implementation of execute."""
        return CallToolResult(content=[], isError=False)


class TestEnumTool(BaseTool):
    """A test tool with enum values in schema."""
    
    name: str = "enum_tool"
    description: str = "A tool with enum values"
    
    # Schema with enum values
    inputSchema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "color": {
                "$ref": "#/$defs/Color"
            }
        },
        "required": ["color"],
        "$defs": {
            "Color": {
                "type": "string",
                "enum": ["red", "green", "blue"],
                "description": "Color selection",
                "default": "blue",
                "title": "Color Option"
            }
        }
    }
    
    async def execute(self, **kwargs) -> CallToolResult:
        """Test implementation of execute."""
        return CallToolResult(content=[], isError=False)


class TestEmptyDescriptionTool(BaseTool):
    """A test tool with an empty description."""
    
    name: str = "empty_desc_tool"
    description: str = ""  # Empty description
    
    inputSchema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "param": {
                "type": "string"
            }
        }
    }
    
    async def execute(self, **kwargs) -> CallToolResult:
        """Test implementation of execute."""
        return CallToolResult(content=[], isError=False)


class TestMCPToolParam(unittest.TestCase):
    
    def test_basic_param_conversion(self):
        """Test conversion of a tool with basic primitive types."""
        tool = TestTool()
        result = tool.to_param()
        
        # Check basic structure
        self.assertEqual(result["type"], "function")
        self.assertIn("function", result)
        
        # Check function details
        func = result["function"]
        self.assertEqual(func["name"], "test_tool_mcp_tool_call")
        self.assertEqual(func["description"], "A test tool for unit testing")
        
        # Check parameters
        params = func["parameters"]
        self.assertEqual(params["type"], "object")
        self.assertIn("properties", params)
        self.assertEqual(params["required"], ["string_param"])
        
        # Check properties
        props = params["properties"]
        self.assertEqual(props["string_param"]["type"], "string")
        self.assertEqual(props["string_param"]["description"], "A string parameter")
        self.assertEqual(props["integer_param"]["type"], "integer")
        self.assertEqual(props["boolean_param"]["type"], "boolean")
    
    def test_nested_schema_conversion(self):
        """Test conversion of a tool with nested object schemas."""
        tool = TestNestedTool()
        result = tool.to_param()
        
        # Check function details
        func = result["function"]
        self.assertEqual(func["name"], "nested_tool_mcp_tool_call")
        
        # Check parameters
        params = func["parameters"]
        self.assertEqual(params["required"], ["user"])
        
        # Check nested objects
        props = params["properties"]
        
        # User object
        self.assertEqual(props["user"]["type"], "object")
        self.assertIn("properties", props["user"])
        user_props = props["user"]["properties"]
        self.assertEqual(user_props["name"]["type"], "string")
        self.assertEqual(user_props["age"]["type"], "integer")
        
        # Options object
        self.assertEqual(props["options"]["type"], "object")
        self.assertIn("properties", props["options"])
        options_props = props["options"]["properties"]
        self.assertEqual(options_props["verbose"]["type"], "boolean")
        self.assertEqual(options_props["limit"]["type"], "integer")
        
        # Note: minimum and maximum properties don't appear to be transferred
        # in the current implementation
    
    def test_enum_conversion(self):
        """Test conversion of a tool with enum values."""
        tool = TestEnumTool()
        result = tool.to_param()
        
        # Check function details
        func = result["function"]
        params = func["parameters"]
        props = params["properties"]
        
        # Check enum properties
        self.assertIn("enum", props["color"])
        self.assertEqual(props["color"]["enum"], ["red", "green", "blue"])
        self.assertEqual(props["color"]["default"], "blue")
        self.assertEqual(props["color"]["title"], "Color Option")
    
    def test_empty_description(self):
        """Test that empty descriptions get a default value."""
        tool = TestEmptyDescriptionTool()
        result = tool.to_param()
        
        func = result["function"]
        self.assertEqual(
            func["description"], 
            "Gets information for the empty_desc_tool_mcp_tool_call function"
        )


if __name__ == "__main__":
    unittest.main() 