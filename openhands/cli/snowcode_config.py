import os
import requests
from typing import Tuple

SNOWCODE_CURRENT_MODEL_URL = os.getenv(
    "SNOWCODE_CURRENT_MODEL_URL",
    "https://api.snowcell.io/models/coding/current",
)

DEFAULT_LLM_MODEL = "hosted_vllm/Meta-Llama-3.1-70B-Instruct"
DEFAULT_BASE_URL = "http://inference.dev.snowcell.io/v1"
DEFAULT_PROVIDER = "hosted_vllm"


def get_llm_config() -> Tuple[str, str]:
    """Returns (llm_model, base_url) from a PUBLIC endpoint.

    - If the server returns "provider/slug", use it directly.
    - If it returns just "slug", prefix with DEFAULT_PROVIDER.
    - On any failure, return (DEFAULT_LLM_MODEL, DEFAULT_BASE_URL).
    """
    # try:
    #     resp = requests.get(SNOWCODE_CURRENT_MODEL_URL, timeout=5)
    #     if resp.status_code == 200 and resp.text:
    #         model_str = resp.text.strip()
    #         llm_model = model_str if "/" in model_str else f"{DEFAULT_PROVIDER}/{model_str}"
    #         return llm_model, DEFAULT_BASE_URL
    # except requests.RequestException:
    #     pass

    return DEFAULT_LLM_MODEL, DEFAULT_BASE_URL
