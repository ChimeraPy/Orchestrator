import json
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
)

from pydantic import BaseModel, ConfigDict, Field, field_validator

import chimerapy.engine as cpe
from chimerapy.orchestrator.registry import get_registered_node


class ManagerConfig(BaseModel):
    logdir: str = Field(..., description="The log directory for the manager.")
    port: int = Field(..., description="The port for the manager.")
    zeroconf: bool = Field(
        default=True, description="If true, enable zeroconf discovery."
    )
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


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
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


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
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class Workers(BaseModel):
    """A list of workers."""

    manager_ip: str = Field(..., description="The manager ip.")
    manager_port: int = Field(..., description="The manager port.")
    instances: List[WorkerConfig] = Field(
        ..., description="The workers to be added."
    )
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


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

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class ChimeraPyPipelineConfig(BaseModel):
    """The pipeline_service config."""

    mode: Literal["preview", "record"] = Field(
        default="record",
        description="The mode of the pipeline_service.",
    )

    name: str = Field(
        default="Pipeline", description="The name of the pipeline"
    )

    description: str = Field(
        default="", description="The description of the pipeline."
    )

    workers: Workers = Field(..., description="The workers to be added.")

    nodes: List[NodeConfig] = Field(
        ..., description="The nodes in the pipeline_service."
    )

    runtime: Optional[int] = Field(
        default=None,
        description="The runtime of the pipeline_service in seconds.",
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

    keep_remote_workers: bool = Field(
        default=True,
        description="If true, keep remote workers after pipeline has finished collection.",
    )

    def instantiate_manager(self) -> cpe.Manager:
        m = cpe.Manager(
            **self.manager_config.model_dump(
                mode="python", exclude={"zeroconf"}
            )
        )
        return m

    def get_registered_node(
        self, name, package
    ) -> Type["WrappedNode"]:  # noqa: F821
        wrapped_node = get_registered_node(name, package)
        return wrapped_node

    def get_cp_graph_map(self) -> Tuple[cpe.Graph, Dict[str, cpe.Node]]:
        created_nodes = {}

        for node_config in self.nodes:
            node_config.kwargs["name"] = node_config.name
            created_nodes[node_config.name] = self.get_registered_node(
                node_config.registry_name,
                package=node_config.package,
            ).instantiate(**node_config.kwargs)

        pipeline = cpe.Graph()
        pipeline.add_nodes_from(list(created_nodes.values()))
        edges = (
            (created_nodes[edge[0]], created_nodes[edge[1]])
            for edge in self.adj
        )

        for edge in edges:
            pipeline.add_edge(*edge)

        return pipeline, created_nodes

    def instantiate_remote_worker(self, worker_id) -> cpe.Worker:
        for wc in self.workers.instances:
            if wc.id == worker_id:
                assert (
                    wc.remote
                ), f"Worker: {worker_id} is not remote, cannot instantiate."
                return cpe.Worker(name=wc.name, id=worker_id, port=0)

        raise ValueError(f"Worker: {worker_id} not found.")

    def list_remote_workers(self):
        remotes = [
            wc.model_dump(mode="json")
            for wc in self.workers.instances
            if wc.remote
        ]
        print(json.dumps(remotes, indent=2))

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @field_validator("nodes", mode="before")
    def validate_nodes(cls, values):
        nodes = []

        for v in values:
            if isinstance(v, str):
                nodes.append(NodeConfig(registry_name=v, name=v))
            elif isinstance(v, dict):
                nodes.append(NodeConfig(**v))
            else:
                nodes.append(v)

        return nodes

    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True
    )
