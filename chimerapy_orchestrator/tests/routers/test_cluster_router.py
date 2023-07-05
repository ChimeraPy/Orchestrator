import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chimerapy_orchestrator.models.cluster_models import (
    ClusterState,
    UpdateMessage,
    UpdateMessageType,
)
from chimerapy_orchestrator.routers.cluster_router import ClusterRouter
from chimerapy_orchestrator.services.cluster_service import ClusterManager
from chimerapy_orchestrator.tests.base_test import BaseTest


@pytest.mark.slow
class TestNetworkRouter(BaseTest):
    @pytest.fixture(scope="class")
    def anyio_backend(self):
        return "asyncio"

    @pytest.fixture(scope="class")
    def manager(self):
        manager = ClusterManager(
            logdir="./logs",
            port=6000,
        )
        return manager

    @pytest.fixture(scope="class")
    async def cluster_manager_and_client(self, manager, anyio_backend):
        asyncio.create_task(manager.start_async_tasks())
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
