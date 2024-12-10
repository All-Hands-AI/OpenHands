from enum import Enum


class FileEditSource(str, Enum):
    LLM_BASED_EDIT = 'llm_based_edit'
    OH_ACI = 'oh_aci'
