import json
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Set, Tuple

import chimerapy as cp
from pydantic import BaseModel, Field


class ManagerConfig(BaseModel):
    logdir: Path = Field(..., description="The log directory for the manager.")
    port: int = Field(..., description="The port for the manager.")


class WorkerConfig(BaseModel):
    name: str = Field(..., description="The name of the worker.")
    id: Optional[str] = Field(default=None, description="The id of the worker.")

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


class ChimeraPyPipelineConfig(BaseModel):
    registered_nodes: ClassVar[Dict[str, cp.Node]] = {}

    workers: Workers = Field(..., description="The workers to be added.")

    nodes: List[str] = Field(..., description="The nodes in the pipeline.")

    adj: List[Tuple[str, str]] = Field(
        ..., description="The edge list of the pipeline graph."
    )

    manager_config: ManagerConfig = Field(
        ..., description="The manager configs."
    )

    mappings: Dict[str, List[str]] = Field(
        ..., description="The delegation mapping of workers to nodes."
    )

    def manager(self) -> cp.Manager:
        return cp.Manager(**self.manager_config.dict())

    def get_registered_node(self, name) -> cp.Node:
        assert name in self.registered_nodes, f"No node named: {name}"
        NodeClass = self.registered_nodes[name]
        return NodeClass()

    def pipeline_graph(
        self,
    ) -> Tuple[cp.Manager, cp.Graph, Dict[str, List[str]], Set[str]]:
        created_nodes = {}
        for node_name in self.nodes:
            created_nodes[node_name] = self.get_registered_node(node_name)

        pipeline = cp.Graph()
        pipeline.add_nodes_from(list(created_nodes.values()))
        edges = map(
            lambda edge: (created_nodes[edge[0]], created_nodes[edge[1]]),
            self.adj,
        )
        for edge in edges:
            pipeline.add_edge(*edge)

        workers = {}
        remote_workers = set()
        for wc in self.workers.instances:
            if not wc.remote:
                wo = cp.Worker(name=wc.name)
                workers[wo.name] = wo
            else:
                remote_workers.add(wc.id)

        manager = self.manager()

        list(
            map(
                lambda w: w.connect(host=manager.host, port=manager.port),
                workers.values(),
            )
        )

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
                return cp.Worker(name=wc.name, id=worker_id)

        raise ValueError(f"Worker: {worker_id} not found.")

    def list_remote_workers(self):
        remotes = list(
            map(
                lambda wc: wc.dict(),
                filter(
                    lambda wc: wc.remote,
                    self.workers.instances,
                ),
            )
        )

        print(json.dumps(remotes, indent=2))

    class Config:
        arbitrary_types_allowed = True
