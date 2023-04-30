import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Type

import chimerapy as cp
from pydantic import BaseModel, Field, validator

from chimerapy_orchestrator.registry import get_registered_node


class ManagerConfig(BaseModel):
    logdir: Path = Field(..., description="The log directory for the manager.")
    port: int = Field(..., description="The port for the manager.")

    class Config:
        allow_extra = False


class NodeConfig(BaseModel):
    registry_name: str = Field(
        ..., description="The name of the node to search in the registry."
    )
    name: str = Field(..., description="The name of the node.")
    kwargs: Dict[str, Any] = Field(
        default={}, description="The kwargs for the node."
    )

    package: Optional[str] = Field(
        default=None, description="The package that registered this node."
    )

    class Config:
        allow_extra = False


class WorkerConfig(BaseModel):
    name: str = Field(..., description="The name of the worker.")
    id: str = Field(default=None, description="The id of the worker.")

    remote: bool = Field(
        default=False,
        description="Indicating the worker is remote and is connected(no creation needed).",
    )

    description: Optional[str] = Field(
        default="", description="The description of the worker."
    )

    class Config:
        allow_extra = False


class Workers(BaseModel):
    """A list of workers."""

    manager_ip: str = Field(..., description="The manager ip.")
    manager_port: int = Field(..., description="The manager port.")
    instances: List[WorkerConfig] = Field(
        ..., description="The workers to be added."
    )

    class Config:
        allow_extra = False


class Timeouts(BaseModel):
    commit_timeout: int = Field(
        default=60,
        description="The timeout for the commit operation in seconds.",
    )

    preview_timeout: int = Field(
        default=20,
        description="The timeout for the preview operation in seconds.",
    )

    record_timeout: int = Field(
        default=20,
        description="The timeout for the record operation in seconds.",
    )

    collect_timeout: int = Field(
        default=20,
        description="The timeout for the commit operation in seconds.",
    )

    stop_timeout: int = Field(
        default=20,
        description="The timeout for the stop operation in seconds.",
    )

    shutdown_timeout: int = Field(
        default=20, description="The timeout for shutdown operation in seconds."
    )

    class Config:
        allow_extra = False
        allow_mutation = False


class ChimeraPyPipelineConfig(BaseModel):
    """The pipeline_service config."""

    mode: Literal["preview", "record"] = Field(
        default="record",
        description="The mode of the pipeline_service.",
    )

    workers: Workers = Field(..., description="The workers to be added.")

    nodes: List[NodeConfig] = Field(
        ..., description="The nodes in the pipeline_service."
    )

    adj: List[Tuple[str, str]] = Field(
        ..., description="The edge list of the pipeline_service graph."
    )

    manager_config: ManagerConfig = Field(
        ..., description="The manager configs."
    )

    mappings: Dict[str, List[str]] = Field(
        ..., description="The delegation mapping of workers to nodes."
    )

    discover_nodes_from: Optional[List[str]] = Field(
        default=[],
        description="The list of modules to discover nodes from. Deprecated. see NodeConfig.package.",
    )

    timeouts: Timeouts = Field(
        default=Timeouts(),
        description="The timeouts for the pipeline operation.",
    )

    def manager(self) -> cp.Manager:
        return cp.Manager(**self.manager_config.dict())

    def get_registered_node(
        self, name, package
    ) -> Type["WrappedNode"]:  # noqa: F821
        wrapped_node = get_registered_node(name, package)
        return wrapped_node

    def pipeline_graph(
        self,
    ) -> Tuple[cp.Manager, cp.Graph, Dict[str, List[str]], Set[str]]:
        created_nodes = {}

        for node_config in self.nodes:
            node_config.kwargs["name"] = node_config.name
            created_nodes[node_config.name] = self.get_registered_node(
                node_config.registry_name,
                package=node_config.package,
            ).instantiate(**node_config.kwargs)

        pipeline = cp.Graph()
        pipeline.add_nodes_from(list(created_nodes.values()))
        edges = (
            (created_nodes[edge[0]], created_nodes[edge[1]])
            for edge in self.adj
        )

        for edge in edges:
            pipeline.add_edge(*edge)

        workers = {}
        remote_workers = set()
        for wc in self.workers.instances:
            if not wc.remote:
                wo = cp.Worker(name=wc.name, port=0)
                workers[wo.name] = wo
            else:
                remote_workers.add(wc.id)

        manager = self.manager()

        [
            w.connect(host=manager.host, port=manager.port)
            for w in workers.values()
        ]

        mp = {}
        for worker in self.mappings:
            try:
                mp[workers[worker].id] = [
                    created_nodes[node_name].id
                    for node_name in self.mappings[worker]
                ]
            except KeyError:
                mp[worker] = [
                    created_nodes[node_name].id
                    for node_name in self.mappings[worker]
                ]
        return manager, pipeline, mp, remote_workers

    def instantiate_remote_worker(self, worker_id) -> cp.Worker:
        for wc in self.workers.instances:
            if wc.id == worker_id:
                assert (
                    wc.remote
                ), f"Worker: {worker_id} is not remote, cannot instantiate."
                return cp.Worker(name=wc.name, id=worker_id, port=0)

        raise ValueError(f"Worker: {worker_id} not found.")

    def list_remote_workers(self):
        remotes = [wc.dict() for wc in self.workers.instances if wc.remote]
        print(json.dumps(remotes, indent=2))

    @validator("nodes", pre=True, each_item=True)
    def validate_nodes(cls, v):
        if isinstance(v, str):
            return NodeConfig(registry_name=v, name=v)
        return v

    class Config:
        arbitrary_types_allowed = True
