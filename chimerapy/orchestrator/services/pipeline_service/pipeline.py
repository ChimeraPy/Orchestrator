from typing import Any, Dict, List, Optional

import networkx as nx

import chimerapy.engine as cpe
from chimerapy.orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)
from chimerapy.orchestrator.models.pipeline_models import WebNode, WrappedNode
from chimerapy.orchestrator.models.registry_models import NodeType
from chimerapy.orchestrator.registry import get_registered_node
from chimerapy.orchestrator.utils import uuid


class NotADagError(ValueError):
    def __init__(self, edge: Dict[str, WrappedNode]) -> None:
        src_identifier = self._get_identifier(edge["source"])
        sink_identifier = self._get_identifier(edge["sink"])
        msg = f"Adding edge {src_identifier} -> {sink_identifier} would create a cycle"
        super().__init__(msg)

    @staticmethod
    def _get_identifier(wrapped_node: WrappedNode) -> str:
        return f"{wrapped_node.NodeClass.__name__}:{wrapped_node.id}"


class EdgeNotFoundError(nx.NetworkXError):
    def __init__(self, edge_id: str) -> None:
        msg = f"Edge {edge_id} does not exist in the pipeline"
        super().__init__(msg)


class NodeNotFoundError(nx.NetworkXError):
    def __init__(self, node_id: str) -> None:
        msg = f"Node {node_id} does not exist in the pipeline"
        super().__init__(msg)


class InvalidNodeError(ValueError):
    def __init__(self, node: Any, reason: str) -> None:
        msg = f"Node {node} is not a valid node: {reason}"
        super().__init__(msg)


class PipelineInstantiationError(Exception):
    """An error that occurs when a pipeline cannot be instantiated."""

    def __init__(self, msg: str):
        super().__init__(msg)


class Pipeline(nx.DiGraph):
    """A directed graph representing a ChimeraPy pipeline without instantiated nodes."""

    def __init__(self, name: str, description: str = "A pipeline") -> None:
        super().__init__()
        self.id = uuid()
        self.name = name
        self.instantiated = False
        self.committed = False
        self.description = description or "A pipeline"
        self.chimerapy_graph = None

    def add_node(
        self,
        node_name: str,
        node_package: Optional[str] = None,
        **kwargs: Dict[str, Any],
    ) -> WrappedNode:
        """Adds a node to the pipeline_service."""
        wrapped_node = get_registered_node(
            node_name, package=node_package
        ).clone(**kwargs)

        super().add_node(wrapped_node.id, wrapped_node=wrapped_node)

        return wrapped_node

    def remove_node(self, node_id: str) -> WrappedNode:
        """Removes a node from the pipeline_service."""
        if node_id not in self.nodes:
            raise NodeNotFoundError(node_id)

        wrapped_node = self.nodes[node_id]["wrapped_node"]
        super().remove_node(node_id)
        return wrapped_node

    def add_edge(
        self, source: str, sink: str, *, edge_id: str = None
    ) -> Dict[str, WrappedNode]:
        """Adds an edge to the pipeline_service."""
        for node in (source, sink):
            if node not in self.nodes:
                raise NodeNotFoundError(node)

        edge = {}
        for node_id, data in self.nodes(data=True):
            wrapped_node: WrappedNode = data["wrapped_node"]
            if node_id == source:
                node_type = wrapped_node.node_type

                if node_type not in {NodeType.SOURCE, NodeType.STEP}:
                    raise InvalidNodeError(
                        f"{node_id}:{wrapped_node.NodeClass.__name__}",
                        "Expected a source or step node, found a sink node",
                    )

                edge["source"] = wrapped_node

            elif node_id == sink:
                node_type = wrapped_node.node_type

                if node_type not in {NodeType.SINK, NodeType.STEP}:
                    raise InvalidNodeError(
                        f"{node_id}:{wrapped_node.NodeClass.__name__}",
                        "Expected a sink or step node, found a source node",
                    )

                edge["sink"] = wrapped_node

        if not self.has_edge(source, sink):
            super().add_edge(
                source,
                sink,
                **{
                    "id": edge_id or uuid(),
                },
            )

        if not self.is_dag():
            super().remove_edge(source, sink)
            raise NotADagError(edge)

        return edge

    def remove_edge(
        self, source: str, sink: str, *, edge_id: str = None
    ) -> Dict[str, WrappedNode]:
        """Removes an edge from the pipeline_service."""
        for node in (source, sink):
            if node not in self.nodes:
                raise NodeNotFoundError(node)

        src_wrapped_node = self.nodes[source]["wrapped_node"]
        dst_wrapped_node = self.nodes[sink]["wrapped_node"]

        if self.has_edge(source, sink):
            if (
                edge_id is not None
                and not self.edges[(source, sink)]["id"] == edge_id
            ):
                raise ValueError(
                    f"Edge {source} -> {sink} does not have id {edge_id}"
                )

            super().remove_edge(source, sink)
        else:
            raise EdgeNotFoundError(edge_id)

        return {"source": src_wrapped_node, "sink": dst_wrapped_node}

    def is_dag(self) -> bool:
        """Returns True if the pipeline_service is a DAG, False otherwise."""
        return nx.is_directed_acyclic_graph(self)

    def to_web_json(self) -> Dict[str, Any]:
        """Returns a JSON representation of the pipeline_service for the web interface."""
        return {
            "id": self.id,
            "name": self.name,
            "instantiated": self.instantiated,
            "committed": self.committed,
            "description": self.description,
            "nodes": [
                data["wrapped_node"].to_web_node().dict()
                for node_id, data in self.nodes(data=True)
            ],
            "edges": [
                {"source": source, "sink": sink, "id": data["id"]}
                for (source, sink, data) in self.edges(data=True)
            ],
        }

    def update_from_web_json(self, web_json: Dict[str, Any]) -> Dict[str, Any]:
        """Update a pipeline from its web json representation."""
        assert self.id == web_json["id"], "Pipeline id mismatch"
        # Check the name of the pipeline
        if web_json["name"] != self.name:
            self.name = web_json["name"]

        # Check the description of the pipeline
        if web_json.get("description") != self.description:
            self.description = web_json["description"]

        # Update Nodes
        for node in web_json["nodes"]:
            wrapped_node = self.nodes[node["id"]]["wrapped_node"]
            wrapped_node.update_from_web_node(WebNode.parse_obj(node))

        # Verify Edges, ToDo: Update edges after chimerapy update
        for edge in web_json["edges"]:
            assert self.has_edge(edge["source"], edge["sink"]), "Edge not found"

        return self.to_web_json()

    def instantiate(self) -> Dict[str, Any]:
        """Instantiates the pipeline."""
        if not self.can_instantiate():
            raise PipelineInstantiationError(
                "Cannot instantiate the pipeline, some nodes don't have worker ids"
            )

        if not self.instantiated:
            cp_graph = cpe.Graph()
            node_to_cp_node = {}
            for node_id, data in self.nodes(data=True):
                wrapped_node: WrappedNode = data["wrapped_node"]
                node = wrapped_node.instantiate()
                cp_graph.add_node(node)
                node_to_cp_node[node_id] = node

            for source, sink, data in self.edges(data=True):  # noqa: B007
                cp_graph.add_edge(
                    node_to_cp_node[source], node_to_cp_node[sink]
                )

            self.instantiated = True
            self.chimerapy_graph = cp_graph
            return self.to_web_json()
        else:
            raise PipelineInstantiationError("Pipeline already instantiated")

    def worker_graph_mapping(self) -> Dict[str, List[str]]:
        worker_graph_mapping = {}

        if not self.instantiated:
            raise ValueError("Pipeline not instantiated")

        for node_id, data in self.nodes(data=True):  # noqa: B007
            wrapped_node: WrappedNode = data["wrapped_node"]

            if wrapped_node.worker_id not in worker_graph_mapping:
                worker_graph_mapping[wrapped_node.worker_id] = []

            worker_graph_mapping[wrapped_node.worker_id].append(
                wrapped_node.instance.id
            )

        return worker_graph_mapping

    def can_instantiate(self) -> bool:
        """Checks if the pipeline can be instantiated."""
        for node_id, data in self.nodes(data=True):  # noqa: B007
            wrapped_node: WrappedNode = data["wrapped_node"]
            if wrapped_node.worker_id is None:
                return False
        return True

    def destroy(self) -> None:
        """Destroys the pipeline instance."""
        self.instantiated = False
        self.committed = False
        self.chimerapy_graph = None
        for node_id, data in self.nodes(data=True):  # noqa: B007
            wrapped_node: WrappedNode = data["wrapped_node"]
            wrapped_node.instance = None

    def __repr__(self) -> str:
        return f"Pipeline<{self.name}>"

    @classmethod
    def from_pipeline_config(
        cls, config: ChimeraPyPipelineConfig
    ) -> "Pipeline":  # TODO: <Monadic?>
        """Creates a pipeline from a ChimeraPyPipelineConfig."""
        pipeline = cls(config.name, config.description)
        node_to_names = {}
        for node in config.nodes:
            kwargs = node.kwargs
            if "name" not in kwargs:
                kwargs["name"] = node.name

            assert (
                kwargs["name"] == node.name
            ), "Node name and kwargs name mismatch"

            wrapped_node = pipeline.add_node(
                node.registry_name, node.package, **node.kwargs
            )
            node_to_names[node.name] = wrapped_node
        for edge in config.adj:
            source, sink = edge
            pipeline.add_edge(node_to_names[source].id, node_to_names[sink].id)

        return pipeline
