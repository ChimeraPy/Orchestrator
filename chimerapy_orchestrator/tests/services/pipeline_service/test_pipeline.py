import pytest
from chimerapy.node import Node
from networkx import NetworkXError

from chimerapy_orchestrator.registry.utils import step_node
from chimerapy_orchestrator.services.pipeline_service.pipeline import (
    NodeNotFoundError,
    NotADagError,
    Pipeline,
)
from chimerapy_orchestrator.tests.base_test import BaseTest
from chimerapy_orchestrator.tests.utils import (
    can_find_mmlapipe_configs,
    get_mmlapipe_configs_root_dir,
    get_pipeline_config,
)


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
        wrapped_node = pipeline.add_node("WebcamNode").unwrap()
        assert wrapped_node.to_web_node().id == wrapped_node.id
        assert (
            wrapped_node.to_web_node().name == wrapped_node.NodeClass.__name__
        )
        assert (
            wrapped_node.to_web_node().registry_name
            == wrapped_node.NodeClass.__name__
        )

    def test_pipeline_removing_nodes(self, pipeline):
        wrapped_node = pipeline.add_node("WebcamNode").unwrap()
        pipeline.remove_node(wrapped_node.id)
        assert wrapped_node.id not in pipeline.nodes

    def test_pipeline_adding_edges(self, pipeline):
        wrapped_node_1 = pipeline.add_node("WebcamNode").unwrap()
        wrapped_node_2 = pipeline.add_node("ShowWindow").unwrap()
        edge = pipeline.add_edge(wrapped_node_1.id, wrapped_node_2.id).unwrap()
        assert edge["source"] is wrapped_node_1
        assert edge["sink"] is wrapped_node_2
        assert (wrapped_node_1.id, wrapped_node_2.id) in pipeline.edges

    def test_pipeline_removing_edges(self, pipeline):
        wrapped_node_1 = pipeline.add_node("WebcamNode").unwrap()
        wrapped_node_2 = pipeline.add_node("ShowWindow").unwrap()
        edge = pipeline.add_edge(wrapped_node_1.id, wrapped_node_2.id).unwrap()
        pipeline.remove_edge(wrapped_node_1.id, wrapped_node_2.id).unwrap()

        assert edge["source"] is wrapped_node_1
        assert edge["sink"] is wrapped_node_2

        assert (wrapped_node_1.id, wrapped_node_2.id) not in pipeline.edges

    def test_pipeline_adding_nodes_error(self, pipeline):
        with pytest.raises(ValueError) as e:
            pipeline.add_node("WebcamNode2").unwrap()
            assert "WebcamNode2 is not a valid node" in str(e.value)

    def test_pipeline_adding_edges_error(self, pipeline):
        wrapped_node_1 = pipeline.add_node("WebcamNode").unwrap()
        wrapped_node_2 = pipeline.add_node("WebcamNode").unwrap()
        with pytest.raises(ValueError) as e:
            pipeline.add_edge(wrapped_node_1.id, wrapped_node_2.id).unwrap()
            assert (
                f"{wrapped_node_2.id}:{wrapped_node_2.__class__.__name__} is not a valid sink node"
                in str(e.value)
            )

        with pytest.raises(ValueError) as e:
            pipeline.add_edge(wrapped_node_2.id, wrapped_node_1.id).unwrap()
            assert (
                f"{wrapped_node_1.id}:{wrapped_node_1.__class__.__name__} is not a valid sink node"
                in str(e.value)
            )

    def test_pipeline_removing_nodes_error(self, pipeline):
        with pytest.raises(NodeNotFoundError) as e:
            pipeline.remove_node("invalid_id").unwrap()
            assert "invalid_id is not a valid node" in str(e.value)

    def test_pipeline_removing_edges_error(self, pipeline):
        wrapped_node_1 = pipeline.add_node("WebcamNode").unwrap()
        wrapped_node_2 = pipeline.add_node("ShowWindow").unwrap()
        with pytest.raises(NetworkXError):
            pipeline.remove_edge(wrapped_node_1.id, wrapped_node_2.id).unwrap()

        with pytest.raises(NodeNotFoundError) as e:
            pipeline.remove_edge("invalid_id", wrapped_node_2.id).unwrap()
            assert "invalid_id is not a valid node" in str(e.value)

    def test_pipeline_dag_error(self, pipeline):
        wrapped_node_1 = pipeline.add_node("WebcamNode").unwrap()
        wrapped_node_2 = pipeline.add_node("DummyStepNode").unwrap()
        wrapped_node_3 = pipeline.add_node("DummyStepNode").unwrap()
        pipeline.add_edge(wrapped_node_1.id, wrapped_node_2.id)
        pipeline.add_edge(wrapped_node_2.id, wrapped_node_3.id)

        with pytest.raises(NotADagError):
            pipeline.add_edge(wrapped_node_3.id, wrapped_node_2.id).unwrap()

    def test_web_json(self, pipeline):
        pipeline.description = "Webcam to ShowWindow"
        wrapped_node_1 = pipeline.add_node("WebcamNode").unwrap()
        wrapped_node_2 = pipeline.add_node("ShowWindow").unwrap()
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

    def test_from_local_camera(self):
        config = get_pipeline_config("local_camera")
        pipeline = Pipeline.from_pipeline_config(config)
        assert pipeline.name == "webcam-demo"

    @pytest.mark.skipif(
        not can_find_mmlapipe_configs(), reason="Can't find mmlapipe"
    )
    def test_from_mmlapipe_displays_pipeline(self):
        config = get_pipeline_config(
            "displays/all_local", get_mmlapipe_configs_root_dir()
        )
        pipeline = Pipeline.from_pipeline_config(config)
        pipeline_dict = pipeline.to_web_json()
        assert pipeline_dict["name"] == "Pipeline"
        for node in pipeline_dict["nodes"]:
            assert node["registry_name"] in [
                "MMLAPIPE_Video",
                "MMLAPIPE_ShowWindows",
            ]
            assert node["kwargs"]["name"] in [
                "test-1",
                "test-2",
                "test-3",
                "test-4",
                "show",
            ]

    @pytest.mark.skipif(
        not can_find_mmlapipe_configs(), reason="Can't find mmlapipe"
    )
    def test_from_mmlapipe_mf_sort(self):
        config = get_pipeline_config(
            "mf_sort/all_local", get_mmlapipe_configs_root_dir()
        )
        pipeline = Pipeline.from_pipeline_config(config)
        pipeline_dict = pipeline.to_web_json()
        assert pipeline_dict["name"] == "Pipeline"
        for node in pipeline_dict["nodes"]:
            assert node["registry_name"] in [
                "MMLAPIPE_MFSortVideo",
                "MMLAPIPE_MFSortVideo",
                "MMLAPIPE_MFSortDetector",
                "MMLAPIPE_BBoxPainter",
                "MMLAPIPE_MFSortTracker",
            ]
            assert node["kwargs"]["name"] in [
                "test-1",
                "test-2",
                "test-3",
                "test-4",
                "mf-sort-detector",
                "bbox-painter-1",
                "mf-sort-tracker-1",
                "mf-sort-tracker-2",
                "mf-sort-tracker-3",
                "mf-sort-tracker-4",
            ]
