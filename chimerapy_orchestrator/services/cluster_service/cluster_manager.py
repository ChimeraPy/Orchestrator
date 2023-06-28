import asyncio

from chimerapy.manager import Manager
from chimerapy.states import ManagerState

from chimerapy_orchestrator.models.cluster_models import UpdateMessage
from chimerapy_orchestrator.monads import Ok, Result
from chimerapy_orchestrator.services.cluster_service.updates_broadcaster import (
    ClusterUpdatesBroadCaster,
)


class ClusterManager:
    def __init__(
        self,
        logdir: str,
        port: int = 9000,
        max_num_of_workers: int = 50,
        publish_logs_via_zmq: bool = False,
    ):
        self._manager = Manager(
            logdir=logdir,
            port=port,
            max_num_of_workers=max_num_of_workers,
            publish_logs_via_zmq=publish_logs_via_zmq,
            enable_api=True,
        )  # Here, we want to refactor this after we have a
        # better understanding of the Manager class into a duck-typed interface.
        self._updates_broadcaster = ClusterUpdatesBroadCaster(
            self._manager.host, self._manager.port
        )

    @property
    def host(self):
        return self._manager.host

    @property
    def port(self):
        return self._manager.port

    def get_network(self) -> Result[ManagerState, Exception]:
        """Get the current state of the network."""
        return Ok(self._manager.state)

    async def start_updates_broadcaster(self) -> None:
        """Begin the updates broadcaster."""
        await self._updates_broadcaster.initialize()
        asyncio.create_task(self._updates_broadcaster.broadcast_updates())

    def shutdown(self) -> None:
        """Shutdown the cluster manager."""
        self._manager.shutdown()

    async def subscribe_to_updates(
        self, q: asyncio.Queue, message: UpdateMessage = None
    ) -> None:
        """Subscribe to updates from the cluster manager."""
        await self._updates_broadcaster.add_client(q, message)

    async def unsubscribe_from_updates(self, q: asyncio.Queue) -> None:
        """Unsubscribe from updates from the cluster manager."""
        await self._updates_broadcaster.remove_client(q)

    def has_shutdown(self) -> bool:
        """Check if the manager has shutdown."""
        return self._manager.has_shutdown

    def is_sentinel(self, msg: str) -> bool:
        """Check if the message is a sentinel message."""
        return msg == self._updates_broadcaster._sentinel

    def enable_zeroconf_discovery(self) -> None:
        """Enable discovery of the cluster manager via zeroconf."""
        self._manager.zeroconf(enable=True)
        self._updates_broadcaster.set_zeroconf_enabled(True)
        asyncio.create_task(self.update_network_status())

    def disable_zeroconf_discovery(self) -> None:
        """Disable discovery of the cluster manager via zeroconf."""
        self._manager.zeroconf(enable=False)
        self._updates_broadcaster.set_zeroconf_enabled(False)
        asyncio.create_task(self.update_network_status())

    async def update_network_status(self) -> None:
        """Update the network status."""
        await self._updates_broadcaster.put_update(self._manager.state)

    def is_zeroconf_discovery_enabled(self) -> bool:
        """Check if zeroconf discovery is enabled."""
        return self._manager.services.zeroconf.enabled
