import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chimerapy.orchestrator.models.cluster_models import (
    ClusterState,
    UpdateMessage,
    UpdateMessageType,
)
from chimerapy.orchestrator.routers.cluster_router import ClusterRouter
from chimerapy.orchestrator.services.cluster_service import ClusterManager
from chimerapy.orchestrator.services.pipeline_service.pipelines import Pipelines
from chimerapy.orchestrator.tests.base_test import BaseTest


@pytest.mark.slow
class TestClusterRouter(BaseTest):
    @pytest.fixture(scope="class")
    def anyio_backend(self):
        return "asyncio"

    @pytest.fixture(scope="class")
    def pipelines(self):
        return Pipelines()

    @pytest.fixture(scope="class")
    def manager(self, pipelines):
        manager = ClusterManager(
            pipeline_service=pipelines,
            logdir="./logs",
            port=6000,
        )
        return manager

    @pytest.fixture(scope="class")
    def pipeline_test(self, pipelines):
        pipeline = pipelines.create_pipeline(
            name="test_pipeline",
            description="test_description",
        ).unwrap()

        screen = pipeline.add_node(node_name="ScreenCaptureNode")
        show = pipeline.add_node("ShowWindow")

        pipeline.add_edge(
            source=screen.id,
            sink=show.id,
        )

        return pipeline

    @pytest.fixture(scope="class")
    async def cluster_manager_and_client(self, manager, anyio_backend):
        await manager.start_async_tasks()
        app = FastAPI()
        app.include_router(ClusterRouter(manager))
        yield manager, TestClient(app)
        manager.shutdown()
        assert manager.has_shutdown()

    @pytest.mark.anyio
    async def test_get_network(self, cluster_manager_and_client):
        manager, client = cluster_manager_and_client

        response = client.get("/cluster/state")
        assert response.status_code == 200
        assert (
            response.json()
            == ClusterState.from_cp_manager_state(
                manager.get_network().unwrap(),
                manager.is_zeroconf_discovery_enabled(),
            ).dict()
        )

        with client.websocket_connect("/cluster/updates") as ws:
            state = ws.receive_json()
            state = UpdateMessage.parse_obj(state)
            assert state.signal == UpdateMessageType.NETWORK_UPDATE

    @pytest.mark.anyio
    async def test_zeroconf_toggle(self, cluster_manager_and_client):
        manager, client = cluster_manager_and_client

        response = client.post("/cluster/zeroconf?enable=true")
        assert response.status_code == 200
        assert response.json() == {"success": True}

        response = client.post("/cluster/zeroconf?enable=false")
        assert response.status_code == 200
        assert response.json() == {"success": True}

    def test_pipeline_instantiate_404(self, cluster_manager_and_client):
        manager, client = cluster_manager_and_client
        response = client.post("/cluster/instantiate/nonexistent_pipeline")
        assert response.status_code == 404

    def test_pipeline_operations_409(self, cluster_manager_and_client):
        manager, client = cluster_manager_and_client

        response = client.post("/cluster/commit")
        assert response.status_code == 409

        response = client.post("/cluster/preview")
        assert response.status_code == 409

        response = client.post("/cluster/record")
        assert response.status_code == 409

        response = client.post("/cluster/stop")
        assert response.status_code == 409

        response = client.post("/cluster/reset")
        assert response.status_code == 409
