from pydantic import BaseModel, Field, SecretStr
from typing import ClassVar, Optional, Union
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.sandbox_config import SandboxConfig
from openhands.core.config.security_config import SecurityConfig
from openhands.core.config.extended_config import ExtendedConfig
from openhands.core.config.agent_config import AgentConfig

class AppConfig(BaseModel):
    """Base application configuration model"""
    llms: dict[str, LLMConfig] = Field(default_factory=dict)
    agents: dict = Field(default_factory=dict)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    extended: ExtendedConfig = Field(default_factory=lambda: ExtendedConfig({}))
    
    # Common configuration fields
    runtime: str = Field(default='docker')
    file_store: str = Field(default='local')
    file_store_path: str = Field(default='/tmp/openhands_file_store')
    workspace_mount_path_in_sandbox: str = Field(default='/workspace')
    cache_dir: str = Field(default='/tmp/cache')
    run_as_openhands: bool = Field(default=True)
    disable_color: bool = Field(default=False)
    debug: bool = Field(default=False)
    
    # MCP Server Configuration
    mcp_servers: dict[str, dict] = Field(
        default_factory=lambda: {
            "default": {
                "enabled": True,
                "port": 8000,
                "host": "localhost",
                "capabilities": ["general"],
                "logging": False
            }
        },
        description="Configure multiple MCP servers with different capabilities"
    )

    defaults_dict: ClassVar[dict] = {}
    model_config = {'extra': 'forbid'}