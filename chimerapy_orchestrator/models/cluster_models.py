from typing import Dict, Literal, Optional

from chimerapy.states import (
    ManagerState,
)
from chimerapy.states import (
    NodeState as _NodeState,
)
from chimerapy.states import (
    WorkerState as _WorkerState,
)
from pydantic import BaseModel, Field


class NodeState(BaseModel):
    id: str
    name: str = ""
    init: bool = False
    connected: bool = False
    ready: bool = False
    finished: bool = False
    port: int = 0

    @classmethod
    def from_cp_node_state(cls, node_state: _NodeState):
        return cls(**node_state.to_dict())

    class Config:
        allow_extra = False
        allow_mutation = False


class WorkerState(BaseModel):
    id: str
    name: str
    port: int = 0
    ip: str = ""
    nodes: Dict[str, NodeState] = Field(default_factory=dict)

    @classmethod
    def from_cp_worker_state(cls, worker_state: _WorkerState):
        state_dict = worker_state.to_dict()
        return cls(
            **state_dict,
        )

    class Config:
        allow_extra = False
        allow_mutation = False


class ClusterState(BaseModel):
    id: str = ""
    ip: str = ""
    port: int = 0
    workers: Dict[str, WorkerState] = Field(default_factory=dict)

    logs_subscription_port: Optional[int] = None
    running: bool = False
    collecting: bool = False
    collection_status: Optional[Literal["PASS", "FAIL"]] = None

    @classmethod
    def from_cp_manager_state(cls, state: ManagerState):
        state_dict = state.to_dict()
        return cls(**state_dict)

    class Config:
        allow_extra = False
        allow_mutation = False
