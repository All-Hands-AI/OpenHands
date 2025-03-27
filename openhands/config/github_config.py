"""GitHub configuration module."""

import os
from typing import Optional

from openhands.config.config import get_config


def get_github_config() -> dict:
    """Get GitHub configuration from config file or environment variables.
    
    Returns:
        dict: GitHub configuration with enterprise_url, api_url, and web_url keys.
    """
    config = get_config()
    github_config = config.get("github", {})
    
    # Get GitHub Enterprise Server configuration
    enterprise_url = os.environ.get(
        "GITHUB_ENTERPRISE_URL", github_config.get("enterprise_url")
    )
    api_url = os.environ.get(
        "GITHUB_API_URL", github_config.get("api_url")
    )
    graphql_url = os.environ.get(
        "GITHUB_GRAPHQL_URL", github_config.get("graphql_url")
    )
    
    # If enterprise_url is set but api_url is not, use default API path
    if enterprise_url and not api_url:
        api_url = f"{enterprise_url}/api/v3"
    
    # If enterprise_url is set but graphql_url is not, use default GraphQL path
    if enterprise_url and not graphql_url:
        graphql_url = f"{enterprise_url}/api/graphql"
    
    return {
        "enterprise_url": enterprise_url,
        "api_url": api_url,
        "graphql_url": graphql_url,
    }


def get_github_api_url() -> Optional[str]:
    """Get GitHub API URL.
    
    Returns:
        Optional[str]: GitHub API URL or None if not configured.
    """
    return get_github_config().get("api_url")


def get_github_enterprise_url() -> Optional[str]:
    """Get GitHub Enterprise URL.
    
    Returns:
        Optional[str]: GitHub Enterprise URL or None if not configured.
    """
    return get_github_config().get("enterprise_url")


def get_github_graphql_url() -> Optional[str]:
    """Get GitHub GraphQL URL.
    
    Returns:
        Optional[str]: GitHub GraphQL URL or None if not configured.
    """
    return get_github_config().get("graphql_url")