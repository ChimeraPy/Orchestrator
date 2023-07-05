import asyncio
import json
from pathlib import Path

from chimerapy.manager import Manager
from chimerapy.states import ManagerState

from chimerapy_orchestrator.models.cluster_models import UpdateMessage
from chimerapy_orchestrator.monads import Ok, Err, Result
from chimerapy_orchestrator.services.cluster_service.updates_broadcaster import (
    ClusterUpdatesBroadCaster, UpdatesBroadcaster
)
from chimerapy_orchestrator.services.pipeline_service.pipelines import Pipeline, Pipelines as PipelineService
from chimerapy_orchestrator.state_machine.fsm import FSM, StateTransitionError


class ClusterManager(FSM):
    def __init__(
        self,
        pipeline_service: PipelineService,
        **manager_kwargs,
    ):
        with (Path(__file__).parent / "states.json").open("r") as f:
            states = json.load(f)

        state_cache, initial_state = super().parse_dict(dict_obj=states)

        super().__init__(
            states=list(state_cache.values()),
            initial_state=state_cache[states["initial_state"]],
            description=states["description"],
        )

        kwargs = {
            "logdir": "logs",
            "port": 9000,
            "max_num_of_workers": 50,
            "publish_logs_via_zmq": False,
            "enable_api": True,
        }
        manager_kwargs.pop("enable_api", None)
        kwargs.update(manager_kwargs)

        # Here, we want to refactor this after we have a
        # better understanding of the Manager class into a duck-typed interface.
        self._manager = Manager(**kwargs)

        self._network_updates_broadcaster = ClusterUpdatesBroadCaster(
            self._manager.host, self._manager.port
        )

        self._sentinel = "STOP"
        self._pipeline_updates_broadcaster = UpdatesBroadcaster(
            self._sentinel
        )

        self._pipeline_service = pipeline_service
        self._active_pipeline = None
        self._futures = []
        self._is_transitioning = False

    @property
    def host(self):
        return self._manager.host

    @property
    def port(self):
        return self._manager.port

    def get_network(self) -> Result[ManagerState, Exception]:
        """Get the current state of the network."""
        return Ok(self._manager.state)

    async def start_async_tasks(self) -> None:
        """Begin the updates broadcaster."""
        await self._network_updates_broadcaster.initialize()
        fut1 = asyncio.ensure_future(self._network_updates_broadcaster.broadcast_updates())
        fut2 = asyncio.ensure_future(self._pipeline_updates_broadcaster.start_broadcast())

        self._futures = [fut1, fut2]

    def shutdown(self) -> None:
        """Shutdown the cluster manager."""
        self._pipeline_updates_broadcaster.enqueue_sentinel()
        self._manager.shutdown()

    async def subscribe_to_network_updates(
        self, q: asyncio.Queue, message: UpdateMessage = None
    ) -> None:
        """Subscribe to network updates from the cluster manager."""
        await self._network_updates_broadcaster.add_client(q, message)

    async def unsubscribe_from_network_updates(self, q: asyncio.Queue) -> None:
        """Unsubscribe from network updates from the cluster manager."""
        await self._network_updates_broadcaster.remove_client(q)

    async def subscribe_to_commit_updates(self, q: asyncio.Queue) -> None:
        """Subscribe to commit updates from the cluster manager."""
        await self._pipeline_updates_broadcaster.add_client(q)

    async def unsubscribe_from_commit_updates(self, q: asyncio.Queue) -> None:
        """Unsubscribe from commit updates from the cluster manager."""
        q.put_nowait(
            self.get_pipeline_update_message()
        )
        await self._pipeline_updates_broadcaster.remove_client(q)

    def has_shutdown(self) -> bool:
        """Check if the manager has shutdown."""
        return self._manager.has_shutdown

    def is_sentinel(self, msg: str) -> bool:
        """Check if the message is a sentinel message."""
        return msg == self._network_updates_broadcaster._sentinel or msg == self._pipeline_updates_broadcaster._sentinel

    def enable_zeroconf_discovery(self) -> None:
        """Enable discovery of the cluster manager via zeroconf."""
        self._manager.zeroconf(enable=True)
        self._network_updates_broadcaster.set_zeroconf_enabled(True)
        asyncio.create_task(self.update_network_status())

    def disable_zeroconf_discovery(self) -> None:
        """Disable discovery of the cluster manager via zeroconf."""
        self._manager.zeroconf(enable=False)
        self._network_updates_broadcaster.set_zeroconf_enabled(False)
        asyncio.create_task(self.update_network_status())

    async def update_network_status(self) -> None:
        """Update the network status."""
        await self._network_updates_broadcaster.put_update(self._manager.state)

    def is_zeroconf_discovery_enabled(self) -> bool:
        """Check if zeroconf discovery is enabled."""
        return self._manager.services.zeroconf.enabled

    def get_pipeline_update_message(self):
        return {
            "pipeline": self._active_pipeline.to_web_json()
            if self._active_pipeline
            else None,
            "fsm": self.to_dict(),
        }

    async def instantiate_pipeline(self, pipeline_id) -> Result[Pipeline, Exception]:
        can, reason = self.can_transition("/activate")

        if self._is_transitioning:
            return Err(Exception("Cannot transition while transitioning"))

        if not can:
            return Err(StateTransitionError(reason))

        return self._pipeline_service.instantiate_pipeline(pipeline_id)

    async def commit_pipeline(self, pipeline_id):
        pass

    async def reset_pipeline(self, pipeline_id):
        pass
