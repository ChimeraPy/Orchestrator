from concurrent.futures import ThreadPoolExecutor

import pytest

from chimerapy.orchestrator.services.pipeline_service.pipelines import (
    PipelineNotFoundError,
    Pipelines,
)
from chimerapy.orchestrator.tests.base_test import BaseTest


class TestPipelines(BaseTest):
    @pytest.fixture
    def pipelines(self):
        return Pipelines()

    def test_create_pipeline(self, pipelines):
        pipeline = pipelines.create_pipeline(
            "test_pipeline", "test_description"
        ).unwrap()
        assert pipeline.id in pipelines._pipelines
        assert pipelines.get_pipeline(pipeline.id).unwrap() is pipeline

    def test_create_pipeline_multiple_threads(self, pipelines):
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    pipelines.create_pipeline,
                    "test_pipeline",
                    "test_description",
                )
                for _ in range(10)
            ]
            for future in futures:
                pipeline = future.result().unwrap()
                assert pipeline.id in pipelines._pipelines
                assert pipelines.get_pipeline(pipeline.id).unwrap() is pipeline

        assert len(pipelines._pipelines) == 10

    def test_get_pipeline(self, pipelines):
        pipeline = pipelines.create_pipeline(
            "test_pipeline", "test_description"
        ).unwrap()

        assert pipelines.get_pipeline(pipeline.id).unwrap() is pipeline

    def test_get_pipeline_error(self, pipelines):
        with pytest.raises(PipelineNotFoundError):
            pipelines.get_pipeline("non_existing_pipeline_id").unwrap()

    def test_get_pipleines_by_name(self, pipelines):
        pipeline = pipelines.create_pipeline(
            "test_pipeline", "test_description"
        )
        pipeline2 = pipelines.create_pipeline(
            "test_pipeline", "test_description"
        )
        assert pipelines.get_pipelines_by_name("test_pipeline").unwrap() == [
            pipeline.unwrap(),
            pipeline2.unwrap(),
        ]

    def test_add_node_to_a_pipeline(self, pipelines):
        pipeline = pipelines.create_pipeline(
            "test_pipeline", "test_description"
        ).unwrap()
        node = pipelines.add_node_to(pipeline.id, "WebcamNode").unwrap()
        assert len(pipeline.nodes) == 1
        assert node.id in pipeline.nodes

    def test_add_node_to_a_pipeline_multiple_threads(self, pipelines):
        pipeline = pipelines.create_pipeline(
            "test_pipeline", "test_description"
        ).unwrap()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(pipeline.add_node, "WebcamNode")
                for _ in range(10)
            ]
            for future in futures:
                node = future.result()
                assert node.id in pipeline.nodes

        assert len(pipeline.nodes) == 10

    def test_add_edge_to_a_pipeline(self, pipelines):
        pipeline = pipelines.create_pipeline(
            "test_pipeline", "test_description"
        ).unwrap()
        node_1 = pipelines.add_node_to(pipeline.id, "WebcamNode").unwrap()
        node_2 = pipelines.add_node_to(pipeline.id, "ShowWindow").unwrap()
        edge = pipelines.add_edge_to(
            pipeline.id, (node_1.id, node_2.id)
        ).unwrap()
        assert edge["source"] is node_1
        assert edge["sink"] is node_2
        assert (node_1.id, node_2.id) in pipeline.edges

    def test_remove_node_from_a_pipeline(self, pipelines):
        pipeline = pipelines.create_pipeline(
            "test_pipeline", "test_description"
        ).unwrap()
        node = pipelines.add_node_to(pipeline.id, "WebcamNode").unwrap()
        pipelines.remove_node_from(pipeline.id, node.id).unwrap()
        assert node.id not in pipeline.nodes

    def test_remove_edge_from_a_pipeline(self, pipelines):
        pipeline = pipelines.create_pipeline(
            "test_pipeline", "test_description"
        ).unwrap()
        node_1 = pipelines.add_node_to(pipeline.id, "WebcamNode").unwrap()
        node_2 = pipelines.add_node_to(pipeline.id, "ShowWindow").unwrap()
        edge = pipelines.add_edge_to(
            pipeline.id, (node_1.id, node_2.id)
        ).unwrap()
        pipelines.remove_edge_from(pipeline.id, (node_1.id, node_2.id)).unwrap()
        assert edge["source"] is node_1
        assert edge["sink"] is node_2
        assert (node_1.id, node_2.id) not in pipeline.edges

    def test_remove_pipeline(self, pipelines):
        pipeline = pipelines.create_pipeline(
            "test_pipeline", "test_description"
        ).unwrap()
        pipelines.remove_pipeline(pipeline.id)
        assert pipeline.id not in pipelines._pipelines

    def test_web_json(self, pipelines):
        node_choices = ["WebcamNode", "ShowWindow"]
        pipelines_created = []
        nodes_created = []
        edge_ids = []
        for j in range(2):
            pipeline = pipelines.create_pipeline(
                f"test_pipeline{j}", "test_description"
            ).unwrap()
            edge = []
            nodes = []
            for node_choice in node_choices:
                n = pipelines.add_node_to(pipeline.id, node_choice).unwrap()
                nodes.append(n)
                edge.append(n.id)

            pipelines.add_edge_to(pipeline.id, (edge[0], edge[1]))
            edge_ids.append(pipeline.edges[(edge[0], edge[1])]["id"])

            nodes_created.append(nodes)
            pipelines_created.append(pipeline)

        assert pipelines.web_json().unwrap() == [
            {
                "id": pipelines_created[0].id,
                "name": "test_pipeline0",
                "instantiated": False,
                "committed": False,
                "description": "test_description",
                "nodes": [
                    {
                        "name": "WebcamNode",
                        "registry_name": "WebcamNode",
                        "id": nodes_created[0][0].id,
                        "kwargs": {
                            "name": "WebcamNode",
                        },
                        "type": "SOURCE",
                        "package": "chimerapy-orchestrator",
                        "worker_id": None,
                    },
                    {
                        "name": "ShowWindow",
                        "registry_name": "ShowWindow",
                        "id": nodes_created[0][1].id,
                        "kwargs": {
                            "name": "ShowWindow",
                        },
                        "type": "SINK",
                        "package": "chimerapy-orchestrator",
                        "worker_id": None,
                    },
                ],
                "edges": [
                    {
                        "id": edge_ids[0],
                        "source": nodes_created[0][0].id,
                        "sink": nodes_created[0][1].id,
                    }
                ],
            },
            {
                "id": pipelines_created[1].id,
                "name": "test_pipeline1",
                "instantiated": False,
                "committed": False,
                "description": "test_description",
                "nodes": [
                    {
                        "name": "WebcamNode",
                        "registry_name": "WebcamNode",
                        "id": nodes_created[1][0].id,
                        "kwargs": {
                            "name": "WebcamNode",
                        },
                        "type": "SOURCE",
                        "package": "chimerapy-orchestrator",
                        "worker_id": None,
                    },
                    {
                        "name": "ShowWindow",
                        "registry_name": "ShowWindow",
                        "id": nodes_created[1][1].id,
                        "kwargs": {
                            "name": "ShowWindow",
                        },
                        "type": "SINK",
                        "package": "chimerapy-orchestrator",
                        "worker_id": None,
                    },
                ],
                "edges": [
                    {
                        "id": edge_ids[1],
                        "source": nodes_created[1][0].id,
                        "sink": nodes_created[1][1].id,
                    }
                ],
            },
        ]
