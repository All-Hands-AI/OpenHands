from pathlib import Path

import toml

from openhands.core.config.kubernetes_config import KubernetesConfig
from openhands.core.config.toml_writer import TOMLConfigWriter


def test_write_kubernetes(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    cfg = KubernetesConfig(
        namespace='oh', ingress_domain='example.com', privileged=True
    )

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_kubernetes(cfg)
    writer.write()

    data = toml.load(cfg_path)
    assert 'kubernetes' in data
    k = data['kubernetes']
    assert k['namespace'] == 'oh'
    assert k['ingress_domain'] == 'example.com'
    assert k['privileged'] is True
