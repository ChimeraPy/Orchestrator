import pytest
from chimerapy.node import Node
from networkx import NetworkXError

from chimerapy_orchestrator.registry.utils import step_node
from chimerapy_orchestrator.services.pipeline_service.pipeline import (
    NotADagError,
    Pipeline,
)
from chimerapy_orchestrator.tests.base_test import BaseTest


class TestPipeline(BaseTest):
    @pytest.fixture
    def pipeline(self):
        p = Pipeline(name="test_pipeline")
        assert p.name == "test_pipeline"
        assert p.description == "A pipeline"
        return p

    @pytest.fixture(scope="session", autouse=True)
    def dummy_step_node(self):
        @step_node(add_to_registry=True)
        class DummyStepNode(Node):
            def __init__(self, name):
                self.name = name

            def step(self, inputs):
                return inputs

        return DummyStepNode

    def test_pipeline_adding_nodes(self, pipeline):
        wrapped_node = pipeline.add_node("WebcamNode")
        assert wrapped_node.to_web_node().id == wrapped_node.id
        assert (
            wrapped_node.to_web_node().name == wrapped_node.NodeClass.__name__
        )
        assert (
            wrapped_node.to_web_node().registry_name
            == wrapped_node.NodeClass.__name__
        )

    def test_pipeline_removing_nodes(self, pipeline):
        wrapped_node = pipeline.add_node("WebcamNode")
        pipeline.remove_node(wrapped_node.id)
        assert wrapped_node.id not in pipeline.nodes

    def test_pipeline_adding_edges(self, pipeline):
        wrapped_node_1 = pipeline.add_node("WebcamNode")
        wrapped_node_2 = pipeline.add_node("ShowWindow")
        edge = pipeline.add_edge(wrapped_node_1.id, wrapped_node_2.id)
        assert edge["source"] is wrapped_node_1
        assert edge["sink"] is wrapped_node_2
        assert (wrapped_node_1.id, wrapped_node_2.id) in pipeline.edges

    def test_pipeline_removing_edges(self, pipeline):
        wrapped_node_1 = pipeline.add_node("WebcamNode")
        wrapped_node_2 = pipeline.add_node("ShowWindow")
        edge = pipeline.add_edge(wrapped_node_1.id, wrapped_node_2.id)
        pipeline.remove_edge(wrapped_node_1.id, wrapped_node_2.id)

        assert edge["source"] is wrapped_node_1
        assert edge["sink"] is wrapped_node_2

        assert (wrapped_node_1.id, wrapped_node_2.id) not in pipeline.edges

    def test_pipeline_adding_nodes_error(self, pipeline):
        with pytest.raises(ValueError) as e:
            pipeline.add_node("WebcamNode2")
            assert "WebcamNode2 is not a valid node" in str(e.value)

    def test_pipeline_adding_edges_error(self, pipeline):
        wrapped_node_1 = pipeline.add_node("WebcamNode")
        wrapped_node_2 = pipeline.add_node("WebcamNode")
        with pytest.raises(ValueError) as e:
            pipeline.add_edge(wrapped_node_1.id, wrapped_node_2.id)
            assert (
                f"{wrapped_node_2.id}:{wrapped_node_2.__class__.__name__} is not a valid sink node"
                in str(e.value)
            )

        with pytest.raises(ValueError) as e:
            pipeline.add_edge(wrapped_node_2.id, wrapped_node_1.id)
            assert (
                f"{wrapped_node_1.id}:{wrapped_node_1.__class__.__name__} is not a valid sink node"
                in str(e.value)
            )

    def test_pipeline_removing_nodes_error(self, pipeline):
        with pytest.raises(ValueError) as e:
            pipeline.remove_node("invalid_id")
            assert "invalid_id is not a valid node" in str(e.value)

    def test_pipeline_removing_edges_error(self, pipeline):
        wrapped_node_1 = pipeline.add_node("WebcamNode")
        wrapped_node_2 = pipeline.add_node("ShowWindow")
        with pytest.raises(NetworkXError):
            pipeline.remove_edge(wrapped_node_1.id, wrapped_node_2.id)

        with pytest.raises(ValueError) as e:
            pipeline.remove_edge("invalid_id", wrapped_node_2.id)
            assert "invalid_id is not a valid node" in str(e.value)

    def test_pipeline_dag_error(self, pipeline):
        wrapped_node_1 = pipeline.add_node("WebcamNode")
        wrapped_node_2 = pipeline.add_node("DummyStepNode")
        wrapped_node_3 = pipeline.add_node("DummyStepNode")
        pipeline.add_edge(wrapped_node_1.id, wrapped_node_2.id)
        pipeline.add_edge(wrapped_node_2.id, wrapped_node_3.id)

        with pytest.raises(NotADagError):
            pipeline.add_edge(wrapped_node_3.id, wrapped_node_2.id)

    def test_web_json(self, pipeline):
        pipeline.description = "Webcam to ShowWindow"
        wrapped_node_1 = pipeline.add_node("WebcamNode")
        wrapped_node_2 = pipeline.add_node("ShowWindow")
        pipeline.add_edge(wrapped_node_1.id, wrapped_node_2.id)
        web_json = pipeline.to_web_json()
        assert web_json["name"] == pipeline.name
        assert len(web_json["nodes"]) == 2
        assert len(web_json["edges"]) == 1
        assert web_json["nodes"][0]["id"] == wrapped_node_1.id
        assert web_json["nodes"][1]["id"] == wrapped_node_2.id
        assert web_json["edges"][0]["source"] == wrapped_node_1.id
        assert web_json["edges"][0]["sink"] == wrapped_node_2.id
        assert web_json["description"] == "Webcam to ShowWindow"
