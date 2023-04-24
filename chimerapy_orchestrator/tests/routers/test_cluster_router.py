import asyncio
import sys

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
from chimerapy_orchestrator.services.pipeline_service import Pipelines
from chimerapy_orchestrator.tests.base_test import BaseTest


@pytest.mark.slow
class TestNetworkRouter(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def event_loop(self):
        policy = asyncio.get_event_loop_policy()
        loop = policy.new_event_loop()
        yield loop
        loop.close()

    @pytest.mark.asyncio
    @pytest.fixture(scope="class")
    async def cluster_manager_and_client(self):
        app = FastAPI()

        manager = ClusterManager(
            pipeline_service=Pipelines(),
            logdir="./logs",
            port=6000,
        )
        app.include_router(ClusterRouter(manager))
        asyncio.create_task(manager.start_updates_broadcaster())
        yield manager, TestClient(app)
        manager.shutdown()
        assert manager.has_shutdown()
        for task in asyncio.all_tasks():
            task.cancel()

    @pytest.mark.asyncio
    async def test_get_network(self, cluster_manager_and_client):
        # Python 3.9 and lower:
        if sys.version_info < (3, 10):
            manager, client = await cluster_manager_and_client.__anext__()
        else:
            manager, client = await anext(cluster_manager_and_client)

        response = client.get("/cluster/state")
        assert response.status_code == 200
        assert (
            response.json()
            == ClusterState.from_cp_manager_state(manager.get_network()).dict()
        )

        with client.websocket_connect("/cluster/updates") as ws:
            state = ws.receive_json()
            state = UpdateMessage.parse_obj(state)
            assert state.signal == UpdateMessageType.NETWORK_UPDATE
