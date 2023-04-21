from typing import Any, Dict, List

from fastapi import APIRouter

from chimerapy_orchestrator.models.pipeline_models import (
    PipelineRequest,
    WebEdge,
    WebNode,
)
from chimerapy_orchestrator.registry import all_nodes
from chimerapy_orchestrator.services.pipeline_service import Pipelines


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

        self.add_api_route(
            "/get/{pipeline_id}",
            self.get_pipeline,
            methods=["GET"],
            response_description="The requested pipeline",
        )

        # Create a new pipeline
        self.add_api_route(
            "/create",
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
            methods=["POST"],
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
            methods=["POST"],
            response_description="The removed edge",
        )

        # Delete a pipeline
        self.add_api_route(
            "/remove/{pipeline_id}",
            self.remove_pipeline,
            methods=["DELETE"],
            response_description="The deleted pipeline",
        )

    async def create_pipeline(
        self, pipeline: PipelineRequest
    ) -> Dict[str, Any]:
        """Create a new pipeline."""
        pipeline = self.pipelines.create_pipeline(
            pipeline.name, description=pipeline.description
        )
        return pipeline.to_web_json()

    async def add_node_to(self, pipeline_id: str, web_node: WebNode) -> WebNode:
        """Add a node to a pipeline."""
        wrapped_node = self.pipelines.add_node_to(
            pipeline_id, web_node.registry_name
        )
        return wrapped_node.to_web_node()

    async def remove_node_from(
        self, pipeline_id: str, web_node: WebNode
    ) -> WebNode:
        """Remove a node from a pipeline."""
        wrapped_node = self.pipelines.remove_node_from(pipeline_id, web_node.id)
        return wrapped_node.to_web_node()

    async def add_edge_to(self, pipeline_id: str, edge: WebEdge) -> WebEdge:
        """Add an edge to a pipeline."""
        created = self.pipelines.add_edge_to(
            pipeline_id, (edge.source.id, edge.sink.id), edge.id
        )
        return WebEdge(
            id=edge.id,
            source=created["source"].to_web_node(),
            sink=created["sink"].to_web_node(),
        )

    async def remove_edge_from(
        self, pipeline_id: str, edge: WebEdge
    ) -> WebEdge:
        """Remove an edge from a pipeline."""
        created = self.pipelines.remove_edge_from(
            pipeline_id, (edge.source.id, edge.sink.id), edge.id
        )
        return WebEdge(
            id=edge.id,
            source=created["source"].to_web_node(),
            sink=created["sink"].to_web_node(),
        )

    async def remove_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Delete a pipeline."""
        pipeline = self.pipelines.remove_pipeline(pipeline_id)
        return pipeline.to_web_json()

    async def list_nodes(self) -> List[WebNode]:
        """Get all nodes."""
        return [node.to_web_node() for node in all_nodes().values()]

    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """Get all pipelines."""
        return self.pipelines.web_json()

    async def get_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Get a pipeline."""
        return self.pipelines.get_pipeline(pipeline_id).to_web_json()
