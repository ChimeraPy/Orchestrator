from typing import Any, Dict, Optional, Type

from chimerapy.node import Node
from pydantic import BaseModel, Field

from chimerapy_orchestrator.utils import uuid


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

    class Config:
        allow_extra = False


class WebEdge(BaseModel):
    """An edge for the web interface."""

    source: WebNode = Field(..., description="The source node of the edge.")

    target: WebNode = Field(..., description="The target node of the edge.")

    class Config:
        allow_extra = False


class WrappedNode(BaseModel):
    """A wrapper for a node."""

    NodeClass: Type[Node] = Field(..., description="The node to be wrapped.")

    kwargs: Dict[str, Any] = Field(
        default={}, description="The kwargs to be passed to the node."
    )

    id: Optional[str] = Field(
        default_factory=uuid, description="The id of the node."
    )

    def instantiate(self, **kwargs) -> Node:
        """Instantiates the node."""
        if "id" not in kwargs:
            kwargs["id"] = uuid()
        return self.NodeClass(**kwargs)

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
        )

    def __repr__(self):
        return f"<WrappedNode: {self.NodeClass.__name__}>"

    class Config:
        allow_extra = False
        arbitrary_types_allowed = True
