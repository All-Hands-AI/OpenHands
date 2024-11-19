import subprocess
from typing import Optional


def get_gpu_generation() -> Optional[str]:
    """Returns the GPU generation, if available."""

    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    generation = result.stdout.strip().split('\n')

    if not generation:
        return None

    return ', '.join([info.strip() for info in generation])
