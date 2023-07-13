from enum import Enum
from typing import Any, ClassVar, Dict, Literal, Optional, Union

from chimerapy.states import (
    ManagerState,
)
from chimerapy.states import (
    NodeState as _NodeState,
)
from chimerapy.states import (
    WorkerState as _WorkerState,
)
from pydantic import BaseModel, ConfigDict, Field


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

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


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

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


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

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


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

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
