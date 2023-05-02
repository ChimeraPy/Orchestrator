from typing import Any, Dict, List, Optional, Tuple

from chimerapy_orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)
from chimerapy_orchestrator.models.pipeline_models import WrappedNode
from chimerapy_orchestrator.services.pipeline_service.pipeline import Pipeline


class Pipelines:
    """A service for managing pipelines."""

    def __init__(self) -> None:
        self._pipelines = {}

    def get_pipeline(
        self, pipeline_id: str, throw: bool = True
    ) -> Optional[Pipeline]:
        """Get a pipeline_service by its ID."""

        if pipeline_id not in self._pipelines:
            if throw:
                raise ValueError(f"Pipeline {pipeline_id} does not exist")
            else:
                return None

        return self._pipelines[pipeline_id]

    def create_pipeline(self, name: str, description: str = None) -> Pipeline:
        """Create a new pipeline_service."""
        pipeline = Pipeline(name=name, description=description)
        self._pipelines[pipeline.id] = pipeline
        return pipeline

    def create_pipeline_from_config(
        self, pipeline_config: ChimeraPyPipelineConfig
    ):
        """Create a new pipeline from a ChimeraPyPipelineConfig."""
        pipeline = Pipeline.from_pipeline_config(pipeline_config)
        self._pipelines[pipeline.id] = pipeline
        return pipeline

    def remove_pipeline(self, pipeline_id: str) -> Pipeline:
        """Delete a pipeline_service."""
        pipeline = self.get_pipeline(pipeline_id)
        self._pipelines.pop(pipeline.id)
        return pipeline

    def add_node_to(
        self,
        pipeline_id: str,
        node_id: str,
        node_package: Optional[str] = None,
        **kwargs,
    ) -> WrappedNode:
        """Add a node to a pipeline_service."""

        pipeline = self.get_pipeline(pipeline_id)
        wrapped_node = pipeline.add_node(node_id, node_package, **kwargs)

        return wrapped_node

    def add_edge_to(
        self, pipeline_id, edge: Tuple[str, str], edge_id: str = None
    ) -> Dict[str, WrappedNode]:
        """Add an edge to a pipeline_service."""
        pipeline = self.get_pipeline(pipeline_id)
        edge = pipeline.add_edge(edge[0], edge[1], edge_id=edge_id)

        return edge

    def remove_edge_from(
        self, pipeline_id, edge: Tuple[str, str], edge_id: str = None
    ) -> Dict[str, WrappedNode]:
        """Remove an edge from a pipeline_service."""
        pipeline = self.get_pipeline(pipeline_id)
        edge = pipeline.remove_edge(edge[0], edge[1], edge_id=edge_id)

        return edge

    def remove_node_from(self, pipeline_id, node_id) -> WrappedNode:
        """Remove a node from a pipeline_service."""
        pipeline = self.get_pipeline(pipeline_id)
        wrapped_node = pipeline.remove_node(node_id)
        return wrapped_node

    def get_pipelines_by_name(self, name: str) -> List[Pipeline]:
        """Get pipeline(s) by name."""
        pipelines = []
        for pipeline in self._pipelines.values():
            if pipeline.name == name:
                pipelines.append(pipeline)

        return pipelines

    def instantiate(self, pipeline_id: str, updater=None) -> None:
        """Instantiate the pipelines."""
        pipeline = self.get_pipeline(pipeline_id)
        pipeline.instantiate(updater=updater)

    def web_json(self, pipeline_id=None) -> List[Dict[str, Any]]:
        """Returns a JSON representation of the pipelines for the web interface."""
        if pipeline_id is None:
            return [
                pipeline.to_web_json() for pipeline in self._pipelines.values()
            ]
        else:
            return [self.get_pipeline(pipeline_id).to_web_json()]
