from typing import Type

from chimerapy.node import Node
from pydantic import BaseModel, Field


class WrappedNode(BaseModel):
    """A wrapper for a node."""

    NodeClass: Type[Node] = Field(..., description="The node to be wrapped.")

    def instantiate(self, **kwargs) -> Node:
        """Instantiates the node."""
        return self.NodeClass(**kwargs)

    @classmethod
    def from_node_class(cls, NodeClass: Type[Node]) -> "WrappedNode":
        wrapped_node = cls(NodeClass=NodeClass)
        return wrapped_node

    class Config:
        allow_extra = False
        arbitrary_types_allowed = True
