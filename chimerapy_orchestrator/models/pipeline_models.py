from typing import Any, Dict, Optional, Type

from chimerapy.node import Node
from pydantic import BaseModel, Field

from chimerapy_orchestrator.models.registry_models import NodeType
from chimerapy_orchestrator.registry import get_node_type
from chimerapy_orchestrator.utils import uuid


class PipelineRequest(BaseModel):
    """A request to create a pipeline."""

    name: str = Field(..., description="The name of the pipeline.")

    description: Optional[str] = Field(
        default=None, description="The description of the pipeline."
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
        return WrappedNode(NodeClass=self.NodeClass, kwargs=kwargs)

    @classmethod
    def from_node_class(
        cls, NodeClass: Type[Node], kwargs=None
    ) -> "WrappedNode":
        if kwargs is None:
            kwargs = {}

        wrapped_node = cls(NodeClass=NodeClass, kwargs=kwargs)

        return wrapped_node

    def to_web_node(self, name: str = None) -> WebNode:
        return WebNode(
            name=name or self.NodeClass.__name__,
            registry_name=self.NodeClass.__name__,
            id=self.id,
            type=get_node_type(self),
            worker_id=self.worker_id,
            instance_id=self.instance_id,
            committed=self.committed,
        )

    def __repr__(self):
        return f"<WrappedNode: {self.NodeClass.__name__}>"

    class Config:
        allow_extra = False
        arbitrary_types_allowed = True
