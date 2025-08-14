import toml
from pathlib import Path

from openhands.core.config.mcp_config import MCPConfig, MCPSSEServerConfig, MCPStdioServerConfig, MCPSHTTPServerConfig
from openhands.core.config.toml_writer import TOMLConfigWriter


def test_write_mcp_lists(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    mcp = MCPConfig(
        sse_servers=[MCPSSEServerConfig(url='https://a.example')],
        stdio_servers=[MCPStdioServerConfig(name='tavily', command='npx', args=['-y','tavily-mcp'])],
        shttp_servers=[MCPSHTTPServerConfig(url='https://b.example')],
    )

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_mcp(mcp)
    writer.write()

    data = toml.load(cfg_path)
    assert 'mcp' in data
    m = data['mcp']
    assert isinstance(m['sse_servers'], list) and m['sse_servers'][0]['url'] == 'https://a.example'
    assert isinstance(m['stdio_servers'], list) and m['stdio_servers'][0]['name'] == 'tavily'
    assert isinstance(m['shttp_servers'], list) and m['shttp_servers'][0]['url'] == 'https://b.example'
