from typing import Any, Dict, List

from pydantic import BaseModel, Field


class WorkerState(BaseModel):
    name: str = Field(..., description="The name of the worker.")
    ip: str = Field(..., description="The ip of the worker.")
    port: int = Field(..., description="The port of the worker.")
    id: int = Field(..., description="The id of the worker.")

    def web_json(self):
        return self.dict()

    class Config:
        allow_extra = False
        allow_mutation = False
        arbitrary_types_allowed = True


class ManagerState(BaseModel):
    name: str = Field(..., description="The name of the manager.")
    ip: str = Field(..., description="The ip of the manager.")
    port: int = Field(..., description="The port of the manager.")
    id: int = Field(..., description="The id of the manager.")
    cluster_state: str = Field(..., description="The state of the cluster.")

    workers: List[WorkerState] = Field(
        default_factory=list, description="The workers that the manager has."
    )

    def web_json(self):
        return self.dict()

    @classmethod
    def from_chimerapy_state_dict(cls, state_dict: Dict[str, Any]):
        pass

    class Config:
        allow_extra = False
        allow_mutation = False
        arbitrary_types_allowed = True


class NodeState(BaseModel):
    pass
