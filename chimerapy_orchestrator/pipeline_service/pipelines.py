from typing import Dict, List, Tuple

from chimerapy_orchestrator.models.pipeline_models import WrappedNode
from chimerapy_orchestrator.pipeline_service.pipeline import Pipeline


class Pipelines:
    """A service for managing pipelines."""

    def __init__(self):
        self._pipelines = {}

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        """Get a pipeline_service by its ID."""
        if pipeline_id not in self._pipelines:
            raise ValueError(f"Pipeline {pipeline_id} does not exist")

        return self._pipelines[pipeline_id]

    def create_pipeline(self, name: str) -> Pipeline:
        """Create a new pipeline_service."""
        pipeline = Pipeline(name=name)
        self._pipelines[pipeline.id] = pipeline
        return pipeline

    def delete_pipeline(self, pipeline_id: str) -> Pipeline:
        """Delete a pipeline_service."""
        pipeline = self.get_pipeline(pipeline_id)
        self._pipelines.pop(pipeline.id)
        return pipeline

    def add_node_to(
        self, pipeline_id: str, node_id: str, **kwargs
    ) -> WrappedNode:
        """Add a node to a pipeline_service."""

        pipeline = self.get_pipeline(pipeline_id)
        wrapped_node = pipeline.add_node(node_id, **kwargs)

        return wrapped_node

    def add_edge_to(
        self, pipeline_id, edge: Tuple[str, str]
    ) -> Dict[str, WrappedNode]:
        """Add an edge to a pipeline_service."""
        pipeline = self.get_pipeline(pipeline_id)
        edge = pipeline.add_edge(edge[0], edge[1])

        return edge

    def remove_edge_from(
        self, pipeline_id, edge: Tuple[str, str]
    ) -> Dict[str, WrappedNode]:
        """Remove an edge from a pipeline_service."""
        pipeline = self.get_pipeline(pipeline_id)
        edge = pipeline.remove_edge(edge[0], edge[1])

        return edge

    def remove_node_from(self, pipeline_id, node_id) -> WrappedNode:
        """Remove a node from a pipeline_service."""
        pipeline = self.get_pipeline(pipeline_id)
        wrapped_node = pipeline.remove_node(node_id)

        return wrapped_node

    def web_json(self, pipeline_id=None) -> List[Dict]:
        """Returns a JSON representation of the pipelines for the web interface."""
        if pipeline_id is None:
            return [
                pipeline.to_web_json() for pipeline in self._pipelines.values()
            ]
        else:
            return [self.get_pipeline(pipeline_id).to_web_json()]
