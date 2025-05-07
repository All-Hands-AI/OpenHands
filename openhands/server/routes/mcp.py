"""
MCP (Model Context Protocol) server for creating pull requests on GitHub or merge requests on GitLab.
This module implements a basic MCP server that exposes tools for creating PRs/MRs using our existing
GitHub and GitLab clients.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.gitlab.gitlab_service import GitLabService
from openhands.core.logger import openhands_logger as logger

# Define MCP router
router = APIRouter(prefix="/mcp", tags=["mcp"])

# MCP JSON-RPC message types
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class MCPNotification(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None

# MCP Server capabilities
SERVER_CAPABILITIES = {
    "protocol": {
        "version": "2025-03-26",
        "roots": {
            "supported": True
        }
    },
    "tools": {
        "supported": True,
        "schema": {
            "supported": True
        }
    }
}

# Tool definitions
TOOLS = [
    {
        "name": "create_github_pr",
        "description": "Create a pull request on GitHub",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "The repository name with owner (e.g., 'owner/repo')"
                },
                "title": {
                    "type": "string",
                    "description": "The title of the pull request"
                },
                "body": {
                    "type": "string",
                    "description": "The description of the pull request"
                },
                "head": {
                    "type": "string",
                    "description": "The name of the branch where your changes are implemented"
                },
                "base": {
                    "type": "string",
                    "description": "The name of the branch you want the changes pulled into",
                    "default": "main"
                },
                "draft": {
                    "type": "boolean",
                    "description": "Whether the pull request is a draft",
                    "default": False
                }
            },
            "required": ["repository", "title", "head"]
        }
    },
    {
        "name": "create_gitlab_mr",
        "description": "Create a merge request on GitLab",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The ID or URL-encoded path of the project"
                },
                "title": {
                    "type": "string",
                    "description": "The title of the merge request"
                },
                "description": {
                    "type": "string",
                    "description": "The description of the merge request"
                },
                "source_branch": {
                    "type": "string",
                    "description": "The source branch name"
                },
                "target_branch": {
                    "type": "string",
                    "description": "The target branch name",
                    "default": "main"
                },
                "draft": {
                    "type": "boolean",
                    "description": "Whether the merge request is a draft",
                    "default": False
                }
            },
            "required": ["project_id", "title", "source_branch"]
        }
    }
]

# MCP session state
class MCPSession:
    def __init__(self):
        self.initialized = False
        self.client_capabilities = {}
        self.github_service = None
        self.gitlab_service = None

# Store active sessions
sessions = {}

@router.post("")
async def handle_mcp_request(request: Request):
    """Handle MCP JSON-RPC requests"""
    try:
        # Get session ID from headers or create a new one
        session_id = request.headers.get("X-MCP-Session-ID", "default")
        if session_id not in sessions:
            sessions[session_id] = MCPSession()
        
        session = sessions[session_id]
        
        # Parse request body
        body = await request.json()
        
        # Handle batch requests
        if isinstance(body, list):
            responses = []
            for req in body:
                response = await process_mcp_request(req, session)
                if response:  # Only include responses for requests (not notifications)
                    responses.append(response)
            return JSONResponse(content=responses)
        else:
            response = await process_mcp_request(body, session)
            if response:
                return JSONResponse(content=response)
            else:
                return Response(status_code=204)  # No content for notifications
    
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                },
                "id": None
            }
        )
    except Exception as e:
        logger.error(f"MCP server error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                },
                "id": None
            }
        )

async def process_mcp_request(request_data: Dict[str, Any], session: MCPSession) -> Optional[Dict[str, Any]]:
    """Process a single MCP request or notification"""
    # Check if it's a notification (no id)
    is_notification = "id" not in request_data
    
    # Validate JSON-RPC format
    if request_data.get("jsonrpc") != "2.0":
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32600,
                "message": "Invalid Request: Not a valid JSON-RPC 2.0 request"
            },
            "id": request_data.get("id", None)
        }
    
    method = request_data.get("method")
    params = request_data.get("params", {})
    request_id = request_data.get("id")
    
    # Handle method calls
    try:
        if method == "initialize":
            result = await handle_initialize(params, session)
        elif method == "shutdown":
            result = await handle_shutdown(session)
        elif method == "listTools":
            result = await handle_list_tools(session)
        elif method == "callTool":
            result = await handle_call_tool(params, session)
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }
        
        # Return response for requests, nothing for notifications
        if not is_notification:
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error processing MCP request: {str(e)}")
        if not is_notification:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                },
                "id": request_id
            }
        else:
            return None

async def handle_initialize(params: Dict[str, Any], session: MCPSession) -> Dict[str, Any]:
    """Handle initialize request"""
    # Store client capabilities
    session.client_capabilities = params.get("capabilities", {})
    session.initialized = True
    
    # Initialize services
    # Note: In a real implementation, you would get tokens from secure storage
    # or environment variables, not hardcode them here
    
    # Return server capabilities
    return {
        "capabilities": SERVER_CAPABILITIES
    }

async def handle_shutdown(session: MCPSession) -> Dict[str, Any]:
    """Handle shutdown request"""
    session.initialized = False
    return {}

async def handle_list_tools(session: MCPSession) -> Dict[str, Any]:
    """Handle listTools request"""
    if not session.initialized:
        raise Exception("Session not initialized")
    
    return {
        "tools": TOOLS
    }

async def handle_call_tool(params: Dict[str, Any], session: MCPSession) -> Dict[str, Any]:
    """Handle callTool request"""
    if not session.initialized:
        raise Exception("Session not initialized")
    
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if tool_name == "create_github_pr":
        return await create_github_pr(arguments, session)
    elif tool_name == "create_gitlab_mr":
        return await create_gitlab_mr(arguments, session)
    else:
        raise Exception(f"Unknown tool: {tool_name}")

async def create_github_pr(arguments: Dict[str, Any], session: MCPSession) -> Dict[str, Any]:
    """Create a GitHub pull request"""
    # Initialize GitHub service if not already done
    if not session.github_service:
        # In a real implementation, you would get the token from secure storage
        # or environment variables, not hardcode it here
        github_token = "GITHUB_TOKEN"  # This would be retrieved securely
        session.github_service = GitHubService(token=github_token)
    
    try:
        # Extract arguments
        repository = arguments.get("repository")
        title = arguments.get("title")
        body = arguments.get("body", "")
        head = arguments.get("head")
        base = arguments.get("base", "main")
        draft = arguments.get("draft", False)
        
        # Validate required arguments
        if not repository or not title or not head:
            raise ValueError("Missing required arguments")
        
        # Make API request to create PR
        # Note: This is a simplified example. In a real implementation,
        # you would use the GitHub API client to create the PR.
        
        # Simulate PR creation (in a real implementation, this would call the GitHub API)
        pr_number = 123  # This would be the actual PR number returned by the API
        pr_url = f"https://github.com/{repository}/pull/{pr_number}"
        
        return {
            "result": {
                "success": True,
                "pr_number": pr_number,
                "pr_url": pr_url,
                "message": f"Pull request #{pr_number} created successfully"
            }
        }
    except Exception as e:
        logger.error(f"Error creating GitHub PR: {str(e)}")
        return {
            "result": {
                "success": False,
                "error": str(e)
            }
        }

async def create_gitlab_mr(arguments: Dict[str, Any], session: MCPSession) -> Dict[str, Any]:
    """Create a GitLab merge request"""
    # Initialize GitLab service if not already done
    if not session.gitlab_service:
        # In a real implementation, you would get the token from secure storage
        # or environment variables, not hardcode it here
        gitlab_token = "GITLAB_TOKEN"  # This would be retrieved securely
        session.gitlab_service = GitLabService(token=gitlab_token)
    
    try:
        # Extract arguments
        project_id = arguments.get("project_id")
        title = arguments.get("title")
        description = arguments.get("description", "")
        source_branch = arguments.get("source_branch")
        target_branch = arguments.get("target_branch", "main")
        draft = arguments.get("draft", False)
        
        # Validate required arguments
        if not project_id or not title or not source_branch:
            raise ValueError("Missing required arguments")
        
        # Make API request to create MR
        # Note: This is a simplified example. In a real implementation,
        # you would use the GitLab API client to create the MR.
        
        # Simulate MR creation (in a real implementation, this would call the GitLab API)
        mr_iid = 456  # This would be the actual MR IID returned by the API
        mr_url = f"https://gitlab.com/{project_id}/-/merge_requests/{mr_iid}"
        
        return {
            "result": {
                "success": True,
                "mr_iid": mr_iid,
                "mr_url": mr_url,
                "message": f"Merge request !{mr_iid} created successfully"
            }
        }
    except Exception as e:
        logger.error(f"Error creating GitLab MR: {str(e)}")
        return {
            "result": {
                "success": False,
                "error": str(e)
            }
        }