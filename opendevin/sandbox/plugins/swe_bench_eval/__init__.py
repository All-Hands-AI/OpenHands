import os
from dataclasses import dataclass
from opendevin.sandbox.plugins.requirement import PluginRequirement

@dataclass
class SWEBenchEvalRequirement(PluginRequirement):
    name: str = 'swe_bench_eval'
    host_src: str = os.path.dirname(os.path.abspath(__file__))
    sandbox_dest: str = '/opendevin/plugins/swe_bench_eval'
    bash_script_path: str = 'swe_env_setup.sh'
