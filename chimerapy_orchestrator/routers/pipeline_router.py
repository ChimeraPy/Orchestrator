from typing import Any, Dict, List

from fastapi import APIRouter

from chimerapy_orchestrator.models.pipeline_models import WebEdge, WebNode
from chimerapy_orchestrator.pipeline_service.pipelines import Pipelines
from chimerapy_orchestrator.registry import all_nodes


class PipelineRouter(APIRouter):
    def __init__(self, pipelines: Pipelines):
        super().__init__(prefix="/pipeline", tags=["pipeline_service"])
        self.pipelines = pipelines
        self.add_api_route(
            "/list",
            self.list_pipelines,
            methods=["GET"],
            response_description="List of all the active pipelines",
        )
        self.add_api_route(
            "/list-nodes",
            self.list_nodes,
            methods=["GET"],
            response_description="List of all the nodes available to add to a pipeline",
        )

        # Create a new pipeline
        self.add_api_route(
            "/create/{name}",
            self.create_pipeline,
            methods=["PUT"],
            response_description="The newly created pipeline",
        )

        # Add/Remove a node to/from a pipeline
        self.add_api_route(
            "/add-node/{pipeline_id}",
            self.add_node_to,
            methods=["POST"],
            response_description="The newly added node",
        )
        self.add_api_route(
            "/remove-node/{pipeline_id}",
            self.remove_node_from,
            methods=["DELETE"],
            response_description="The removed node",
        )

        # Add/Remove an edge to/from a pipeline
        self.add_api_route(
            "/add-edge/{pipeline_id}",
            self.add_edge_to,
            methods=["POST"],
            response_description="The newly added edge",
        )
        self.add_api_route(
            "/remove-edge/{pipeline_id}",
            self.remove_edge_from,
            methods=["DELETE"],
            response_description="The removed edge",
        )

        # Delete a pipeline
        self.add_api_route(
            "/delete/{pipeline_id}",
            self.delete_pipeline,
            methods=["DELETE"],
            response_description="The deleted pipeline",
        )

    async def create_pipeline(self, name: str) -> Dict[str, Any]:
        """Create a new pipeline."""
        pipeline = self.pipelines.create_pipeline(name)
        return pipeline.to_web_json()

    async def add_node_to(self, pipeline_id: str, web_node: WebNode) -> WebNode:
        """Add a node to a pipeline."""
        wrapped_node = self.pipelines.add_node_to(
            pipeline_id, web_node.registry_name
        )
        return wrapped_node.to_web_node()

    async def remove_node_from(self, pipeline_id: str, node_id: str) -> WebNode:
        """Remove a node from a pipeline."""
        wrapped_node = self.pipelines.remove_node_from(pipeline_id, node_id)
        return wrapped_node.to_web_node()

    async def add_edge_to(self, pipeline_id: str, edge: WebEdge) -> WebEdge:
        """Add an edge to a pipeline."""
        edge = self.pipelines.add_edge_to(
            pipeline_id, (edge.source.id, edge.target.id)
        )
        return WebEdge(
            source=edge["source"].to_web_node(),
            target=edge["target"].to_web_node(),
        )

    async def remove_edge_from(
        self, pipeline_id: str, edge: WebEdge
    ) -> WebEdge:
        """Remove an edge from a pipeline."""
        edge = self.pipelines.remove_edge_from(
            pipeline_id, (edge.source.id, edge.target.id)
        )
        return WebEdge(
            source=edge["source"].to_web_node(),
            target=edge["target"].to_web_node(),
        )

    async def delete_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Delete a pipeline."""
        pipeline = self.pipelines.delete_pipeline(pipeline_id)
        return pipeline.to_web_json()

    async def list_nodes(self) -> List[WebNode]:
        """Get all nodes."""
        return [node.to_web_node() for node in all_nodes().values()]

    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """Get all pipelines."""
        return self.pipelines.web_json()
