from pathlib import Path

import toml

from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.condenser_config import LLMSummarizingCondenserConfig
from openhands.core.config.kubernetes_config import KubernetesConfig
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPStdioServerConfig,
)
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.config.utils import load_from_toml
from openhands.core.config.toml_writer import TOMLConfigWriter


def test_roundtrip_mixed_sections(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    # 1) Write a complex configuration
    writer = TOMLConfigWriter(str(cfg_path))

    # core values
    writer.update_core({'debug': True})

    # default llm and named override
    writer.update_llm_base(LLMConfig(model='gpt-4o-mini'))
    writer.update_llm_named('fast', LLMConfig(model='gpt-4o-mini', temperature=0.2))

    # agent with condenser (which has nested LLMConfig)
    agent = AgentConfig()
    agent.condenser = LLMSummarizingCondenserConfig(
        llm_config=LLMConfig(model='gpt-4o-mini', temperature=0.1),
        keep_first=2,
        max_size=25,
    )
    writer.update_agent_base(agent)

    # MCP and k8s
    mcp = MCPConfig(
        stdio_servers=[
            MCPStdioServerConfig(name='tavily', command='npx', args=['-y', 'tavily-mcp'])
        ]
    )
    writer.update_mcp(mcp)

    k8s = KubernetesConfig(namespace='oh', ingress_domain='example.com')
    writer.update_kubernetes(k8s)

    writer.write()

    # 2) Read with loader and assert equivalence of key fields
    cfg = OpenHandsConfig()
    load_from_toml(cfg, str(cfg_path))

    assert cfg.debug is True

    # llm defaults and named
    assert 'llm' in cfg.llms
    assert 'fast' in cfg.llms
    assert cfg.llms['fast'].temperature == 0.2

    # agent condenser nested llm
    default_agent = cfg.get_agent_config()
    assert default_agent.condenser.type == 'llm'
    assert default_agent.condenser.keep_first == 2

    # mcp and k8s round-trip
    assert cfg.mcp is not None
    assert len(cfg.mcp.stdio_servers or []) == 1
    assert cfg.kubernetes.namespace == 'oh'
