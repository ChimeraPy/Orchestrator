from typing import Any, Dict

import networkx as nx

from chimerapy_orchestrator.models.pipeline_models import WrappedNode
from chimerapy_orchestrator.models.registry_models import NodeType
from chimerapy_orchestrator.registry import get_node_type, get_registered_node
from chimerapy_orchestrator.utils import uuid


class NotADagError(ValueError):
    def __init__(self, edge: Dict[str, WrappedNode]) -> None:
        src_identifier = self._get_identifier(edge["source"])
        sink_identifier = self._get_identifier(edge["sink"])
        msg = f"Adding edge {src_identifier} -> {sink_identifier} would create a cycle"
        super().__init__(msg)

    @staticmethod
    def _get_identifier(wrapped_node: WrappedNode) -> str:
        return f"{wrapped_node.NodeClass.__name__}:{wrapped_node.id}"


class Pipeline(nx.DiGraph):
    """A directed graph representing a ChimeraPy pipeline without instantiated nodes."""

    def __init__(self, name: str, description: str = "A pipeline") -> None:
        super().__init__()
        self.id = uuid()
        self.name = name
        self.instantiated = False
        self.description = description or "A pipeline"
        self.chimerapy_graph = None

    def add_node(self, node_name: str, **kwargs: Dict[str, Any]) -> WrappedNode:
        """Adds a node to the pipeline_service."""
        wrapped_node = get_registered_node(node_name).clone(**kwargs)
        super().add_node(wrapped_node.id, wrapped_node=wrapped_node)
        return wrapped_node

    def remove_node(self, node_id: str) -> WrappedNode:
        """Removes a node from the pipeline_service."""
        if node_id not in self.nodes:
            raise ValueError(f"{node_id} does not exist in the pipeline")

        wrapped_node = self.nodes[node_id]["wrapped_node"]
        super().remove_node(node_id)
        return wrapped_node

    def add_edge(self, source: str, sink: str) -> Dict[str, WrappedNode]:
        """Adds an edge to the pipeline_service."""
        for node in (source, sink):
            if node not in self.nodes:
                raise ValueError(f"{node} is not a valid node")
        edge = {}
        for node_id, data in self.nodes(data=True):
            wrapped_node = data["wrapped_node"]
            if node_id == source:
                node_type = get_node_type(wrapped_node)

                if node_type not in {NodeType.SOURCE, NodeType.STEP}:
                    raise ValueError(
                        f"{node_id}:{wrapped_node.NodeClass.__name__} is not a valid source node"
                    )
                edge["source"] = wrapped_node

            elif node_id == sink:
                node_type = get_node_type(wrapped_node)

                if node_type not in {NodeType.SINK, NodeType.STEP}:
                    raise ValueError(
                        f"{node_id}:{wrapped_node.NodeClass.__name__} is not a valid sink node"
                    )

                edge["sink"] = wrapped_node

        super().add_edge(source, sink)

        if not self.is_dag():
            super().remove_edge(source, sink)
            raise NotADagError(edge)

        return edge

    def remove_edge(self, source: str, sink: str) -> Dict[str, WrappedNode]:
        """Removes an edge from the pipeline_service."""
        for node in (source, sink):
            if node not in self.nodes:
                raise ValueError(f"{node} is not a valid node")

        src_wrapped_node = self.nodes[source]["wrapped_node"]
        dst_wrapped_node = self.nodes[sink]["wrapped_node"]

        super().remove_edge(source, sink)

        return {"source": src_wrapped_node, "sink": dst_wrapped_node}

    def is_dag(self) -> bool:
        """Returns True if the pipeline_service is a DAG, False otherwise."""
        return nx.is_directed_acyclic_graph(self)

    def __repr__(self) -> str:
        return f"Pipeline<{self.name}>"

    def to_web_json(self) -> Dict[str, Any]:
        """Returns a JSON representation of the pipeline_service for the web interface."""
        return {
            "id": self.id,
            "name": self.name,
            "instantiated": self.instantiated,
            "description": self.description,
            "nodes": [
                data["wrapped_node"].to_web_node().dict()
                for node_id, data in self.nodes(data=True)
            ],
            "edges": [
                {"source": source, "sink": sink} for source, sink in self.edges
            ],
        }
