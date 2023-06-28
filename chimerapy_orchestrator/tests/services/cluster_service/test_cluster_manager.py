import asyncio

import pytest
from chimerapy.utils import get_ip_address

from chimerapy_orchestrator.models.cluster_models import (
    UpdateMessage,
    UpdateMessageType,
)
from chimerapy_orchestrator.services.cluster_service import ClusterManager
from chimerapy_orchestrator.tests.base_test import BaseTest


@pytest.mark.slow
class TestClusterManager(BaseTest):
    @pytest.fixture(scope="class")
    def anyio_backend(self):
        return "asyncio"

    @pytest.fixture(scope="class")
    def cluster_manager(self, anyio_backend):
        manager = ClusterManager(
            logdir="./logs",
            port=0,
        )
        yield manager
        manager.shutdown()
        assert manager.has_shutdown()

    def test_get_network(self, cluster_manager):
        assert cluster_manager.get_network().map(
            lambda n: n.to_dict()
        ).unwrap() == {
            "id": "Manager",
            "ip": get_ip_address(),
            "port": cluster_manager._manager.port,  # pylint: disable=protected-access
            "workers": {},
            "logs_subscription_port": None,
        }

    @pytest.mark.timeout(30)
    @pytest.mark.anyio
    async def test_network_updates(self, cluster_manager, anyio_backend):
        client_queue = asyncio.Queue()
        asyncio.create_task(cluster_manager.start_updates_broadcaster())

        await cluster_manager.subscribe_to_updates(
            client_queue,
            UpdateMessage(
                data=None,
                signal=UpdateMessageType.NETWORK_UPDATE,
            ),
        )

        assert client_queue.qsize() == 1
        msg = await client_queue.get()
        assert msg["signal"] == UpdateMessageType.NETWORK_UPDATE
        assert msg["data"] is None

    @pytest.mark.anyio
    async def test_zeroconf(self, cluster_manager):
        assert cluster_manager.is_zeroconf_discovery_enabled() is False
        cluster_manager.enable_zeroconf_discovery()
        assert cluster_manager.is_zeroconf_discovery_enabled() is True
        cluster_manager.disable_zeroconf_discovery()
        assert cluster_manager.is_zeroconf_discovery_enabled() is False
