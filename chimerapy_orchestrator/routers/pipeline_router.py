from typing import Any, Dict, List

from fastapi import APIRouter

from chimerapy_orchestrator.models.pipeline_models import (
    NodesPlugin,
    PipelineRequest,
    WebEdge,
    WebNode,
)
from chimerapy_orchestrator.registry import (
    check_registry,
    get_all_nodes,
    importable_packages,
)
from chimerapy_orchestrator.routers.error_mappers import get_mapping
from chimerapy_orchestrator.services.pipeline_service import Pipelines


class PipelineRouter(APIRouter):
    def __init__(self, pipelines: Pipelines):
        super().__init__(prefix="/pipeline", tags=["pipeline_service"])
        self.pipelines = pipelines

        # Nodes and plugins
        self.add_api_route(
            "/list-nodes",
            self.list_nodes,
            methods=["GET"],
            response_description="List of all the nodes available to add to a pipeline",
        )

        # Import from plugins
        self.add_api_route(
            "/plugins",
            self.installable_plugins,
            methods=["GET"],
            response_description="List of all the nodes available to add to a pipeline",
            description="Import nodes from plugins",
        )

        self.add_api_route(
            "/install-plugin/{package}",
            self.install_plugin,
            methods=["POST"],
            response_description="List of all the nodes available to add to a pipeline",
        )

        # Pipeline operations
        self.add_api_route(
            "/list",
            self.list_pipelines,
            methods=["GET"],
            response_description="List of all the active pipelines",
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

        # Update a pipeline
        self.add_api_route(
            "/update/{pipeline_id}",
            self.update_pipeline,
            methods=["POST"],
            response_description="The updated pipeline",
        )

    async def create_pipeline(
        self, pipeline: PipelineRequest
    ) -> Dict[str, Any]:
        """This method creates a new pipeline.

        The pipeline request is a json object with the following structure:
        - **name**: the name of the pipeline
        - **description**: the description of the pipeline
        - **config**: the configuration of the pipeline

        Note that a pipeline can be created using a chimerapy orchestrator configuration json (config). Or simply by
        providing a name and an optional description. Precedence is given to the config json.
        """
        if pipeline.config is not None:
            pipeline = self.pipelines.create_pipeline_from_config(
                pipeline.config
            )
        else:
            pipeline = self.pipelines.create_pipeline(
                pipeline.name, description=pipeline.description
            )

        return (
            pipeline.map(lambda p: p.to_web_json())
            .map_error(lambda err: get_mapping(err).to_fastapi())
            .unwrap()
        )

    async def add_node_to(self, pipeline_id: str, web_node: WebNode) -> WebNode:
        """Add a node to an existing pipeline.

        The request body should a json object with the following required fields:
        - **name**: the name of the node (same as the registry name)
        - **registry_name**: the name of the node in the registry
        - **package**: the package of the node

        The response will return the newly added node. If the pipeline does not exist, a 404 error will be returned.
        """
        wrapped_node = self.pipelines.add_node_to(
            pipeline_id, web_node.registry_name, web_node.package
        )

        return (
            wrapped_node.map(lambda n: n.to_web_node())
            .map_error(lambda err: get_mapping(err).to_fastapi())
            .unwrap()
        )

    async def remove_node_from(
        self, pipeline_id: str, web_node: WebNode
    ) -> WebNode:
        """Remove a node from an existing pipeline.

        The request body should a json object with the following required fields:
        - **id**: the id of the node to remove
        - **name**: the name of the node (same as the registry name)
        - **registry_name**: the name of the node in the registry

        The response will return the removed node as json. If the pipeline/node does not exist, a 404 error will be returned.
        """
        wrapped_node = self.pipelines.remove_node_from(pipeline_id, web_node.id)

        return (
            wrapped_node.map(lambda n: n.to_web_node())
            .map_error(lambda err: get_mapping(err).to_fastapi())
            .unwrap()
        )

    async def add_edge_to(self, pipeline_id: str, edge: WebEdge) -> WebEdge:
        """Add an edge to a pipeline."""
        return (
            self.pipelines.add_edge_to(
                pipeline_id, (edge.source.id, edge.sink.id), edge.id
            )
            .map(
                lambda c: WebEdge(
                    id=edge.id,
                    source=c["source"].to_web_node(),
                    sink=c["sink"].to_web_node(),
                )
            )
            .map_error(lambda err: get_mapping(err).to_fastapi())
            .unwrap()
        )

    async def remove_edge_from(
        self, pipeline_id: str, edge: WebEdge
    ) -> WebEdge:
        """Remove an edge from a pipeline.

        The request body should a json object with the following required fields:
        - **id**: the id of the edge to remove
        - **source**: the source node of the edge
        - **sink**: the sink node of the edge

        The response will return the removed edge as json. If the pipeline, edge or the nodes do not exist, a 404 error will be returned.
        """
        return (
            self.pipelines.remove_edge_from(
                pipeline_id, (edge.source.id, edge.sink.id), edge.id
            )
            .map(
                lambda c: WebEdge(
                    id=edge.id,
                    source=c["source"].to_web_node(),
                    sink=c["sink"].to_web_node(),
                )
            )
            .map_error(lambda err: get_mapping(err).to_fastapi())
            .unwrap()
        )

    async def remove_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Delete a pipeline.

        The response will return the deleted pipeline as json. If the pipeline does not exist, a 404 error will be returned.
        """
        return (
            self.pipelines.remove_pipeline(pipeline_id)
            .map(lambda p: p.to_web_json())
            .map_error(lambda err: get_mapping(err).to_fastapi())
            .unwrap()
        )

    async def list_nodes(self) -> List[WebNode]:
        """Get all nodes.

        The response will return a list of all nodes (that can be used to create pipelines) as json.
        """
        return [node.to_web_node() for node in get_all_nodes()]

    async def install_plugin(self, package: str) -> List[WebNode]:
        """Import all nodes from a package.

        The response will return a list of all nodes (that can be used to create pipelines) as json.
        """
        try:
            check_registry(package)
        except Exception as e:
            raise e

        return [node.to_web_node() for node in get_all_nodes()]

    async def installable_plugins(self) -> List[NodesPlugin]:
        """Get all importable packages.

        The response will return a list of all importable packages as json.
        """
        return [
            NodesPlugin.from_plugin_registry(package_name=package_name)
            for package_name in importable_packages()
        ]

    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """Get all pipelines.

        The response will return a list of all pipelines as json.
        """
        return self.pipelines.web_json().unwrap()

    async def get_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Get a pipeline.

        The response will return the pipeline as json. If the pipeline does not exist, a 404 error will be returned.
        """
        return (
            self.pipelines.get_pipeline(pipeline_id)
            .map(lambda p: p.to_web_json())
            .map_error(lambda err: get_mapping(err).to_fastapi())
            .unwrap()
        )

    async def update_pipeline(
        self, pipeline_id: str, pipeline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a pipeline.

        The response will return the pipeline as json. If the pipeline does not exist, a 404 error will be returned.
        """
        updated = self.pipelines.update_from_web_json(pipeline_id, pipeline)
        return updated.unwrap()
