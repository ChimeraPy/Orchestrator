import inspect

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chimerapy.orchestrator.models.pipeline_models import NodesPlugin
from chimerapy.orchestrator.registered_nodes.nodes import WebcamNode
from chimerapy.orchestrator.registry import get_all_nodes, importable_packages
from chimerapy.orchestrator.routers.pipeline_router import PipelineRouter
from chimerapy.orchestrator.services.pipeline_service import Pipelines
from chimerapy.orchestrator.tests.base_test import BaseTest
from chimerapy.orchestrator.tests.utils import get_pipeline_config
from chimerapy.orchestrator.utils import uuid


class TestPipelineRouter(BaseTest):
    @pytest.fixture(scope="class")
    def pipeline_client(self):
        app = FastAPI()
        app.include_router(PipelineRouter(Pipelines()))
        yield TestClient(app)

    def test_installable_plugins(self, pipeline_client):
        response = pipeline_client.get("/pipeline/plugins")
        assert response.status_code == 200
        assert response.json() == [
            NodesPlugin.from_plugin_registry(
                package_name=package_name
            ).model_dump(mode="json")
            for package_name in importable_packages()
        ]

    def test_get_pipelines(self, pipeline_client):
        response = pipeline_client.get("/pipeline/list")
        assert response.status_code == 200
        assert response.json() == []

    def test_install_plugin(self, pipeline_client):
        response = pipeline_client.post(
            "/pipeline/install-plugin/plugin-nodes-package"
        )
        assert response.status_code == 200
        node_names = [node["name"] for node in response.json()]
        assert "ANode" in node_names
        assert "BNode" in node_names

    def test_list_nodes(self, pipeline_client):
        response = pipeline_client.get("/pipeline/list-nodes")
        assert response.status_code == 200
        assert len(response.json()) == len(get_all_nodes())

    def test_create_pipeline(self, pipeline_client):
        pipeline = pipeline_client.put(
            "/pipeline/create",
            json={"name": "test_pipeline", "description": "test_description"},
        )
        assert pipeline.status_code == 200
        json_response = pipeline.json()
        assert json_response["name"] == "test_pipeline"
        assert json_response["description"] == "test_description"
        assert json_response["id"] is not None
        assert json_response["nodes"] == []
        assert json_response["edges"] == []

    def test_create_pipeline_from_config(self, pipeline_client):
        config = get_pipeline_config("local_camera")
        pipeline = pipeline_client.put(
            "/pipeline/create",
            json={"config": config.model_dump(mode="json")},
        )
        assert pipeline.status_code == 200
        json_response = pipeline.json()
        assert json_response["name"] == "webcam-demo"
        assert (
            json_response["description"]
            == "A demo of the webcam node and the show window node"
        )
        assert json_response["id"] is not None
        assert len(json_response["nodes"]) == 2
        assert len(json_response["edges"]) == 1

    def test_list_pipelines(self, pipeline_client):
        pipelines = pipeline_client.get("/pipeline/list")
        assert pipelines.status_code == 200
        assert len(pipelines.json()) == 2

    def test_node_edge_operations(self, pipeline_client):
        pipeline = pipeline_client.get("/pipeline/list").json()[0]
        pipeline_id = pipeline["id"]

        # Add nodes
        webcam_node = pipeline_client.post(
            f"/pipeline/add-node/{pipeline_id}",
            json={"name": "WebcamNode", "registry_name": "WebcamNode"},
        )

        assert webcam_node.status_code == 200
        webcam_node_json = webcam_node.json()
        assert webcam_node_json["name"] == "WebcamNode"
        assert webcam_node_json["registry_name"] == "WebcamNode"
        assert webcam_node_json["id"] is not None
        assert webcam_node_json["type"] == "SOURCE"

        show_window_node = pipeline_client.post(
            f"/pipeline/add-node/{pipeline_id}",
            json={
                "name": "ShowWindow",
                "registry_name": "ShowWindow",
                "kwargs": {"name": "test"},
            },
        )

        assert show_window_node.status_code == 200
        show_window_node_json = show_window_node.json()
        assert show_window_node_json["name"] == "test"
        assert show_window_node_json["registry_name"] == "ShowWindow"
        assert show_window_node_json["id"] is not None
        assert show_window_node_json["type"] == "SINK"

        # Add edges
        edge_id = uuid()
        edge = pipeline_client.post(
            f"/pipeline/add-edge/{pipeline_id}",
            json={
                "source": webcam_node_json,
                "sink": show_window_node_json,
                "id": edge_id,
            },
        )

        assert edge.status_code == 200
        edge_json = edge.json()
        assert edge_json["source"]["id"] == webcam_node_json["id"]
        assert edge_json["sink"]["id"] == show_window_node_json["id"]
        assert edge_json["id"] == edge_id

        # Remove edge
        edge = pipeline_client.post(
            f"/pipeline/remove-edge/{pipeline_id}",
            json={
                "source": webcam_node_json,
                "sink": show_window_node_json,
                "id": edge_id,
            },
        )
        assert edge.status_code == 200
        edge_json = edge.json()
        assert edge_json["source"]["id"] == webcam_node_json["id"]
        assert edge_json["sink"]["id"] == show_window_node_json["id"]
        assert edge_json["id"] == edge_id

        # Remove node
        node = pipeline_client.post(
            f"/pipeline/remove-node/{pipeline_id}", json=webcam_node_json
        )

        assert node.status_code == 200
        node_json = node.json()
        assert node_json["id"] == webcam_node_json["id"]
        assert node_json["name"] == webcam_node_json["name"]
        assert node_json["registry_name"] == webcam_node_json["registry_name"]
        assert node_json["type"] == webcam_node_json["type"]

        pipeline_json = pipeline_client.get(
            f"/pipeline/get/{pipeline_id}"
        ).json()

        # Update pipeline
        for node in pipeline_json["nodes"]:
            node["name"] = "UpdatedNodeName"
            node["worker_id"] = uuid()

        pipeline_json["name"] = "UpdatedName"

        pipeline = pipeline_client.post(
            f"/pipeline/update/{pipeline_json['id']}", json=pipeline_json
        )

        assert pipeline.status_code == 200
        pipeline_json_updated = pipeline.json()
        assert pipeline_json_updated["id"] == pipeline_id
        assert pipeline_json_updated["name"] == "UpdatedName"
        assert pipeline_json_updated["description"] == "test_description"
        assert pipeline_json_updated["nodes"] == pipeline_json["nodes"]

        # Remove pipeline

        assert pipeline.status_code == 200
        pipeline_json = pipeline.json()
        assert pipeline_json["id"] == pipeline_id
        assert pipeline_json["name"] == "UpdatedName"
        assert pipeline_json["description"] == "test_description"

    def test_node_info(self, pipeline_client):
        response = pipeline_client.get(
            "/pipeline/node/source-code/?registry_name=WebcamNode&package=chimerapy-orchestrator"
        )
        assert response.status_code == 200
        assert response.json() == {
            "source_code": inspect.getsource(inspect.getmodule(WebcamNode)),
            "module": inspect.getmodule(WebcamNode).__name__,
            "doc": WebcamNode.__doc__,
        }
