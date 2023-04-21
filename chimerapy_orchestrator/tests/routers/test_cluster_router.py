import chimerapy as cp
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chimerapy_orchestrator.models.cluster_models import ClusterState
from chimerapy_orchestrator.routers.cluster_router import ClusterRouter
from chimerapy_orchestrator.services.cluster_service import ClusterManager
from chimerapy_orchestrator.tests.base_test import BaseTest


@pytest.mark.slow
class TestNetworkRouter(BaseTest):
    @pytest.fixture(scope="class")
    def cluster_manager_and_client(self):
        app = FastAPI()
        manager = ClusterManager(
            logdir="./logs",
            port=0,
        )
        app.include_router(ClusterRouter(manager))
        yield manager, TestClient(app)
        manager.shutdown()
        assert manager.has_shutdown()

    def test_get_network(self, cluster_manager_and_client):
        manager, client = cluster_manager_and_client
        response = client.get("/cluster/state")
        assert response.status_code == 200
        assert (
            response.json()
            == ClusterState.from_cp_manager_state(manager.get_network()).dict()
        )

    def test_get_network_updates(self, cluster_manager_and_client):
        manager, client = cluster_manager_and_client

        def connect_worker():
            w = cp.Worker(
                name="test_worker",
            )
            w.connect(
                manager.host,
                manager.port,
            )

            return w

        with client.websocket_connect("/cluster/updates") as ws:
            message = ws.receive_json()
            assert manager.is_cluster_update_message(message)
            assert (
                message["data"]
                == ClusterState.from_cp_manager_state(
                    manager.get_network()
                ).dict()
            )
            worker = connect_worker()
            message = ws.receive_json()
            assert manager.is_cluster_update_message(message)
            assert (
                message["data"]["workers"][worker.id] == worker.state.to_dict()
            )
