import pytest
from chimerapy.utils import get_ip_address

from chimerapy_orchestrator.services.cluster_service import ClusterManager
from chimerapy_orchestrator.services.pipeline_service import Pipelines
from chimerapy_orchestrator.tests.base_test import BaseTest


@pytest.mark.slow
class TestClusterManager(BaseTest):
    @pytest.fixture(scope="class")
    def cluster_manager(self):
        manager = ClusterManager(
            pipeline_service=Pipelines(),
            logdir="./logs",
            port=0,
        )
        yield manager
        manager.shutdown()
        assert manager.has_shutdown()

    def test_get_network(self, cluster_manager):
        assert cluster_manager.get_network().to_dict() == {
            "id": "Manager",
            "ip": get_ip_address(),
            "port": cluster_manager._manager.port,  # pylint: disable=protected-access
            "workers": {},
            "logs_subscription_port": None,
            "running": False,
            "collecting": False,
            "collection_status": None,
        }
