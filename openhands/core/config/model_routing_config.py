from pydantic import BaseModel, Field


class ModelRoutingConfig(BaseModel):
    reasoning_llm_config_name: str = Field(default='reasoning_model')
    judge_llm_config_name: str = Field(default='judge_model')
