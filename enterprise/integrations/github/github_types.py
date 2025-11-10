from enum import Enum

from pydantic import BaseModel


class WorkflowRunStatus(Enum):
    FAILURE = 'failure'
    COMPLETED = 'completed'
    PENDING = 'pending'

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


class WorkflowRun(BaseModel):
    id: str
    name: str
    status: WorkflowRunStatus

    model_config = {'use_enum_values': True}


class WorkflowRunGroup(BaseModel):
    runs: dict[str, WorkflowRun]
