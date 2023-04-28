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
    @pytest.fixture(scope="class")
    def event_loop_class(self):
        policy = asyncio.get_event_loop_policy()
        loop = policy.new_event_loop()
        yield loop
        loop.close()

    @pytest.fixture(scope="class")
    def manager(self):
        manager = ClusterManager(
            pipeline_service=Pipelines(),
            logdir="./logs",
            port=6000,
        )
        return manager

    @pytest.fixture(scope="class")
    async def cluster_manager_and_client(self, manager, event_loop_class):
        broadcast_task = event_loop_class.create_task(
            manager.start_async_tasks()
        )
        app = FastAPI()
        app.include_router(ClusterRouter(manager))
        yield manager, TestClient(app)
        manager.shutdown()
        await broadcast_task
        assert manager.has_shutdown()
        assert broadcast_task.done()
        for task in asyncio.all_tasks(event_loop_class):
            await task
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
