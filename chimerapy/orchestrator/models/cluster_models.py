from enum import Enum
from typing import Any, Dict, Literal, Optional, Union

from pydantic import BaseModel, Field

from chimerapy.engine.states import (
    ManagerState,
)
from chimerapy.engine.states import (
    NodeState as _NodeState,
)
from chimerapy.engine.states import (
    WorkerState as _WorkerState,
)


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
    zeroconf_discovery: bool = False

    @classmethod
    def from_cp_manager_state(
        cls, state: ManagerState, zeroconf_discovery: bool
    ):
        state_dict = state.to_dict()
        return cls(**state_dict, zeroconf_discovery=zeroconf_discovery)

    class Config:
        allow_extra = False
        allow_mutation = False


class UpdateMessageType(str, Enum):
    NETWORK_UPDATE = "NETWORK_UPDATE"
    SHUTDOWN = "SHUTDOWN"


class UpdateMessage(BaseModel):
    signal: UpdateMessageType = Field(
        ..., description="The signal of the update message."
    )
    data: Union[ClusterState, None] = Field(
        default=None, description="The data of the update message."
    )

    @classmethod
    def from_updates_dict(
        cls,
        msg: Dict[str, Any],
        signal: UpdateMessageType,
        zeroconf_discovery: bool,
    ) -> "UpdateMessage":
        if (data := msg.get("data")) is not None:
            data = ManagerState.from_dict(data)
            data = ClusterState.from_cp_manager_state(data, zeroconf_discovery)

        return cls(signal=signal, data=data)

    class Config:
        allow_extra = False
        allow_mutation = False
