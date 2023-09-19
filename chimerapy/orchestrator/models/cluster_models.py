from enum import Enum
from typing import Any, ClassVar, Dict, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from chimerapy.engine.states import (
    ManagerState,
)
from chimerapy.engine.states import (
    NodeState as _NodeState,
)
from chimerapy.engine.states import (
    WorkerState as _WorkerState,
)


class RegisteredMethod(BaseModel):
    name: str
    style: Literal["concurrent", "blocking", "reset"] = "concurrent"
    params: Dict[str, str] = Field(default_factory=dict)


class NodeDiagnostics(BaseModel):
    timestamp: str
    latency: float
    payload_size: float
    memory_usage: float
    cpu_usage: float
    num_of_steps: int


class NodeState(BaseModel):
    id: str
    name: str = ""
    port: int = 0
    fsm: Literal[
        "NULL",
        "INITIALIZED",
        "CONNECTED",
        "READY",
        "PREVIEWING",
        "RECORDING",
        "STOPPED",
        "SAVED",
        "SHUTDOWN",
    ]
    registered_methods: Dict[str, RegisteredMethod] = Field(
        default_factory=dict
    )
    logdir: Optional[str] = None
    diagnostics: NodeDiagnostics

    @classmethod
    def from_cp_node_state(cls, node_state: _NodeState):
        node_state_dict = node_state.to_dict()
        node_state_dict["logdir"] = (
            str(node_state_dict["logdir"])
            if node_state_dict["logdir"] is not None
            else None
        )
        return cls(**node_state.to_dict())

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


class WorkerState(BaseModel):
    id: str
    name: str
    port: int = 0
    ip: str = ""
    nodes: Dict[str, NodeState] = Field(default_factory=dict)
    tempfolder: str = ""

    @classmethod
    def from_cp_worker_state(cls, worker_state: _WorkerState):
        state_dict = worker_state.to_dict()
        state_dict["tempfolder"] = str(state_dict["tempfolder"])
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
    log_sink_enabled: bool = False
    zeroconf_discovery: bool = False
    logdir: str = None

    @classmethod
    def from_cp_manager_state(
        cls, state: ManagerState, zeroconf_discovery: bool
    ):
        state_dict = state.to_dict()
        state_dict["logdir"] = str(state_dict["logdir"])
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
