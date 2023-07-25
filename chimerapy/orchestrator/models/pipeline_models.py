import importlib
import inspect
from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, Field

from chimerapy.engine.node import Node
from chimerapy.orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)
from chimerapy.orchestrator.models.registry_models import NodeType
from chimerapy.orchestrator.registry import discovered_nodes, plugin_registry
from chimerapy.orchestrator.utils import uuid


class NodeSourceCode(BaseModel):
    """A node's source code."""

    source_code: str = Field(..., description="The source code of the node.")
    module: str = Field(..., description="The module of the node.")
    doc: Optional[str] = Field(
        default=None, description="The docstring of the node."
    )
    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_registry(cls, registry_name, package) -> "NodeSourceCode":
        """Create a NodeSourceCode from a registry_name and package."""
        wrapped_node = discovered_nodes.get_node(registry_name, package=package)
        source_code = inspect.getsource(
            inspect.getmodule(wrapped_node.NodeClass)
        )
        return cls(
            source_code=source_code,
            module=wrapped_node.NodeClass.__module__,
            doc=wrapped_node.NodeClass.__doc__,
        )


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

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


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

    package: Optional[str] = Field(
        default=None, description="The package that registered this node."
    )

    worker_id: Optional[str] = Field(
        default=None, description="The id of the worker that runs this node."
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class WebEdge(BaseModel):
    """An edge for the web interface."""

    id: Optional[str] = Field(
        default_factory=uuid, description="The id of the edge."
    )

    source: WebNode = Field(..., description="The source node of the edge.")

    sink: WebNode = Field(..., description="The target node of the edge.")

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


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

    node_type: Optional[NodeType] = Field(
        default=None, description="The type of the node."
    )

    registry_name: str = Field(
        ..., description="The name of the node in the registry."
    )

    package: Optional[str] = Field(
        default=None, description="The package that registered this node."
    )

    name: Optional[str] = Field(
        default=None, description="The name of the node."
    )

    worker_id: Optional[str] = Field(
        default=None, description="The id of the worker that runs this node."
    )

    @property
    def instantiated(self) -> bool:
        return self.instance is not None

    def instantiate(self, **kwargs) -> Node:
        """Instantiates the node."""
        kwargs = {**self.kwargs, **kwargs}

        if "name" not in kwargs:
            kwargs["name"] = self.name or self.NodeClass.__name__

        self.instance = self.NodeClass(**kwargs)
        return self.instance

    def clone(self, **kwargs) -> "WrappedNode":
        """Creates a new WrappedNode from another one."""
        if kwargs is None:
            kwargs = {}
        if kwargs == {}:
            kwargs = self.kwargs
        return WrappedNode(
            name=self.name,
            NodeClass=self.NodeClass,
            node_type=self.node_type,
            registry_name=self.registry_name,
            kwargs=kwargs,
            package=self.package,
            worker_id=self.worker_id,
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

        wrapped_node = cls(
            NodeClass=NodeClass,
            name=NodeClass.__name__,
            kwargs=kwargs,
            node_type=node_type,
            registry_name=registry_name,
        )

        return wrapped_node

    def to_web_node(self) -> WebNode:
        return WebNode(
            name=self.name or self.NodeClass.__name__,
            registry_name=self.registry_name,
            id=self.id,
            type=self.node_type,
            package=self.package,
            kwargs=self.kwargs,
            worker_id=self.worker_id,
        )

    def update_from_web_node(self, web_node: WebNode) -> None:
        if self.instantiated:
            raise RuntimeError("Cannot update instantiated node.")

        if self.id != web_node.id:
            raise ValueError("Cannot update node with different id.")

        self.name = web_node.name
        self.kwargs = web_node.kwargs
        self.node_type = web_node.type
        self.registry_name = web_node.registry_name
        self.package = web_node.package
        self.worker_id = web_node.worker_id

    def __repr__(self):
        return f"<WrappedNode: {self.NodeClass.__name__}>"

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", arbitrary_types_allowed=True
    )


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

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")
