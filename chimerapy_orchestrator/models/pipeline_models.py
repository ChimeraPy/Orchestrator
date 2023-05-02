import importlib
from typing import Any, Dict, List, Optional, Type

from chimerapy.node import Node
from pydantic import BaseModel, Field

from chimerapy_orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)
from chimerapy_orchestrator.models.registry_models import NodeType
from chimerapy_orchestrator.registry import plugin_registry
from chimerapy_orchestrator.utils import uuid


class PipelineRequest(BaseModel):
    """A request to create a pipeline."""

    name: Optional[str] = Field(
        default=None, description="The name of the pipeline."
    )

    description: Optional[str] = Field(
        default=None, description="The description of the pipeline."
    )

    config: Optional[ChimeraPyPipelineConfig] = Field(
        default=None,
        description="The configuration of the pipeline.",
    )

    class Config:
        allow_extra = False


class WebNode(BaseModel):
    """A node for the web interface."""

    name: str = Field(..., description="The name of the node.")

    registry_name: str = Field(
        ..., description="The name of the node in the registry."
    )

    id: Optional[str] = Field(default=None, description="The id of the node.")

    kwargs: Optional[Dict[str, Any]] = Field(
        default={}, description="The kwargs of the node."
    )

    type: Optional[NodeType] = Field(
        default=None, description="The type of the node."
    )

    worker_id: Optional[str] = Field(
        default=None,
        description="The id of the worker once the node get committed.",
    )

    instance_id: Optional[str] = Field(
        default=None,
        description="The id of the instance once the node get committed.",
    )

    committed: bool = Field(
        default=False,
        description="Whether the node has been committed to a worker.",
    )

    package: Optional[str] = Field(
        default=None, description="The package that registered this node."
    )

    class Config:
        allow_extra = False


class WebEdge(BaseModel):
    """An edge for the web interface."""

    id: Optional[str] = Field(
        default_factory=uuid, description="The id of the edge."
    )

    source: WebNode = Field(..., description="The source node of the edge.")

    sink: WebNode = Field(..., description="The target node of the edge.")

    class Config:
        allow_extra = False


class WrappedNode(BaseModel):
    """A wrapper for a node."""

    NodeClass: Type[Node] = Field(..., description="The node to be wrapped.")

    instance: Optional[Node] = Field(
        default=None, description="The instance for this wrapped node"
    )

    kwargs: Dict[str, Any] = Field(
        default={}, description="The kwargs to be passed to the node."
    )

    id: Optional[str] = Field(
        default_factory=uuid, description="The id of the node."
    )

    worker_id: Optional[str] = Field(
        default=None,
        description="The id of the worker once the node get committed.",
    )

    committed: bool = Field(
        default=False,
        description="Whether the node has been committed to a worker.",
    )

    node_type: Optional[NodeType] = Field(
        default=None, description="The type of the node."
    )

    registry_name: str = Field(
        ..., description="The name of the node in the registry."
    )

    package: Optional[str] = Field(
        default=None, description="The package that registered this node."
    )

    @property
    def name(self):
        return self.instance.name if self.instance else self.NodeClass.__name__

    @property
    def instance_id(self) -> Optional[str]:
        return self.instance.id if self.instance else None

    @property
    def instantiated(self) -> bool:
        return self.instance is not None

    def instantiate(self, **kwargs) -> Node:
        """Instantiates the node."""
        self.instance = self.NodeClass(**kwargs)
        return self.instance

    def clone(self, **kwargs) -> "WrappedNode":
        """Creates a new WrappedNode from another one."""
        if kwargs is None:
            kwargs = {}
        if kwargs == {}:
            kwargs = self.kwargs
        return WrappedNode(
            NodeClass=self.NodeClass,
            node_type=self.node_type,
            registry_name=self.registry_name,
            kwargs=kwargs,
            package=self.package,
        )

    @classmethod
    def from_node_class(
        cls,
        NodeClass: Type[Node],
        node_type: NodeType,
        registry_name: str,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> "WrappedNode":
        if kwargs is None:
            kwargs = {}
        return WrappedNode(
            NodeClass=NodeClass,
            node_type=node_type,
            registry_name=registry_name,
            kwargs=kwargs,
        )

    def to_web_node(self, name: str = None) -> WebNode:
        return WebNode(
            name=name or self.NodeClass.__name__,
            registry_name=self.registry_name or self.NodeClass.__name__,
            id=self.id,
            type=self.node_type,
            worker_id=self.worker_id,
            instance_id=self.instance_id,
            committed=self.committed,
            package=self.package,
            kwargs=self.kwargs,
        )

    def __repr__(self):
        return f"<WrappedNode: {self.NodeClass.__name__}>"

    class Config:
        allow_extra = False
        arbitrary_types_allowed = True


class NodesPlugin(BaseModel):
    """A plugin that can be installed."""

    name: str = Field(..., description="The name of the plugin.")

    package: str = Field(..., description="The package of the plugin.")

    nodes: List[str] = Field(
        ..., description="The nodes that this plugin provides."
    )

    description: Optional[str] = Field(
        default=None, description="The description of the plugin."
    )

    version: str = Field(..., description="The version of the plugin.")

    @classmethod
    def from_plugin_registry(cls, package_name):
        if package_name not in plugin_registry:
            raise ValueError(f"Plugin {package_name} not found in registry.")

        nodes = plugin_registry[package_name]["nodes"]
        description = plugin_registry[package_name].get("description", None)
        node_names = [name.rsplit(":")[-1] for name in nodes]
        try:
            version = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            version = "N/A"

        return cls(
            name=package_name,
            package=package_name,
            nodes=node_names,
            version=version,
            description=description,
        )

    class Config:
        allow_extra = False
