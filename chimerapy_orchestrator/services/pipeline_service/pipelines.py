from typing import Any, Dict, List, Optional, Tuple

from chimerapy_orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)
from chimerapy_orchestrator.models.pipeline_models import WrappedNode
from chimerapy_orchestrator.monads import Err, Ok, Result
from chimerapy_orchestrator.services.pipeline_service.pipeline import Pipeline


class PipelineNotFoundError(Exception):
    """Raised when a pipeline_service is not found."""

    def __init__(self, pipeline_id: str) -> None:
        super().__init__(f"Pipeline {pipeline_id} not found")


class Pipelines:
    """A service for managing pipelines."""

    def __init__(self) -> None:
        self._pipelines = {}

    def get_pipeline(self, pipeline_id: str) -> Result[Pipeline, Exception]:
        """Get a pipeline_service by its ID."""
        if pipeline_id not in self._pipelines:
            return Err(PipelineNotFoundError(pipeline_id))

        return Ok(self._pipelines[pipeline_id])

    def create_pipeline(
        self, name: str, description: str = None
    ) -> Result[Pipeline, Exception]:
        """Create a new pipeline_service."""
        pipeline = Pipeline(name=name, description=description)
        self._pipelines[pipeline.id] = pipeline
        return Ok(pipeline)

    def create_pipeline_from_config(
        self, pipeline_config: ChimeraPyPipelineConfig
    ) -> Result[Pipeline, Exception]:
        """Create a new pipeline from a ChimeraPyPipelineConfig."""
        pipeline = Pipeline.from_pipeline_config(pipeline_config)
        self._pipelines[pipeline.id] = pipeline
        return Ok(pipeline)

    def remove_pipeline(self, pipeline_id: str) -> Result[Pipeline, Exception]:
        """Delete a pipeline_service."""
        return self.get_pipeline(pipeline_id).map(
            lambda p: self._pipelines.pop(p.id)
        )

    def add_node_to(
        self,
        pipeline_id: str,
        node_id: str,
        node_package: Optional[str] = None,
        **kwargs,
    ) -> Result[WrappedNode, Exception]:
        """Add a node to a pipeline_service."""
        return self.get_pipeline(pipeline_id).map(
            lambda p: p.add_node(node_id, node_package, **kwargs)
        )

    def add_edge_to(
        self, pipeline_id, edge: Tuple[str, str], edge_id: str = None
    ) -> Result[Dict[str, WrappedNode], Exception]:
        """Add an edge to a pipeline_service."""
        return self.get_pipeline(pipeline_id).map(
            lambda p: p.add_edge(edge[0], edge[1], edge_id=edge_id)
        )

    def remove_edge_from(
        self, pipeline_id, edge: Tuple[str, str], edge_id: str = None
    ) -> Result[Dict[str, WrappedNode], Exception]:
        """Remove an edge from a pipeline_service."""

        return self.get_pipeline(pipeline_id).map(
            lambda p: p.remove_edge(edge[0], edge[1], edge_id=edge_id)
        )

    def remove_node_from(
        self, pipeline_id, node_id
    ) -> Result[WrappedNode, Exception]:
        """Remove a node from a pipeline_service."""
        return self.get_pipeline(pipeline_id).map(
            lambda p: p.remove_node(node_id)
        )

    def get_pipelines_by_name(
        self, name: str
    ) -> Result[List[Pipeline], Exception]:
        """Get pipeline(s) by name."""
        pipelines = []
        for pipeline in self._pipelines.values():
            if pipeline.name == name:
                pipelines.append(pipeline)

        return Ok(pipelines)

    def web_json(
        self, pipeline_id=None
    ) -> Result[List[Dict[str, Any]], Exception]:
        """Returns a JSON representation of the pipelines for the web interface."""
        if pipeline_id is None:
            return Ok(
                [
                    pipeline.to_web_json()
                    for pipeline in self._pipelines.values()
                ]
            )
        else:
            return self.get_pipeline(pipeline_id).map(lambda p: p.to_web_json())

    def update_from_web_json(
        self, pipeline_id, web_json: Dict[str, Any]
    ) -> Result[Dict[str, Any], Exception]:
        """Update the pipelines from a JSON representation of the pipelines for the web interface."""
        return self.get_pipeline(pipeline_id).map(
            lambda p: p.update_from_web_json(web_json)
        )

    async def instantiate_pipeline(
        self, pipeline_id
    ) -> Result[Dict[str, Any], Exception]:
        """Instantiate a pipeline."""
        pipeline = self.get_pipeline(pipeline_id)
        result = pipeline.ok()
        if result.is_none():
            return pipeline
        else:
            try:
                p = result.unwrap()
                instance = p.instantiate()
                return Ok(instance)
            except Exception as e:
                return Err(e)
