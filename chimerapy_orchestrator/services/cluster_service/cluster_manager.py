import asyncio
import json
from pathlib import Path
from typing import Dict, Union

from chimerapy.manager import Manager
from chimerapy.states import ManagerState

from chimerapy_orchestrator.models.cluster_models import UpdateMessage
from chimerapy_orchestrator.monads import Err, Ok, Result
from chimerapy_orchestrator.services.cluster_service.updates_broadcaster import (
    ClusterUpdatesBroadCaster,
    UpdatesBroadcaster,
)
from chimerapy_orchestrator.services.pipeline_service import Pipeline, Pipelines
from chimerapy_orchestrator.state_machine.fsm import FSM, StateTransitionError


class PipelineNotFoundError(Exception):
    """Raised when a pipeline is not found in the cluster."""

    pass


class ClusterManager(FSM):
    def __init__(self, pipeline_service: Pipelines, **manager_kwargs):
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

        self._commit_updates_broadcaster = UpdatesBroadcaster(self._sentinel)

        self._pipeline_service = pipeline_service
        self.active_pipeline = None
        self._manager_busy = False
        self.futures = []

    @property
    def host(self):
        return self._manager.host

    @property
    def port(self):
        return self._manager.port

    def get_network(self) -> ManagerState:
        """Get the current state of the network."""
        return self._manager.state

    async def start_async_tasks(self):
        """Begin the updates broadcaster."""
        await self._network_updates_broadcaster.initialize()
        fut1 = asyncio.ensure_future(
            self._network_updates_broadcaster.broadcast_updates()
        )
        fut2 = asyncio.ensure_future(
            self._commit_updates_broadcaster.start_broadcast()
        )
        self.futures = [fut1, fut2]

    def shutdown(self):
        """Shutdown the cluster manager."""
        self._commit_updates_broadcaster.enqueue_sentinel()
        self._manager.shutdown()

    async def subscribe_to_network_updates(
        self, q: asyncio.Queue, message: UpdateMessage = None
    ):
        """Subscribe to updates from the cluster manager."""
        await self._network_updates_broadcaster.add_client(q, message)

    async def unsubscribe_from_network_updates(self, q: asyncio.Queue):
        """Unsubscribe from updates from the cluster manager."""
        await self._network_updates_broadcaster.remove_client(q)

    async def subscribe_to_commit_updates(self, q: asyncio.Queue):
        """Subscribe to updates from the cluster manager."""
        q.put_nowait(
            {
                "pipeline": self.active_pipeline.to_web_json()
                if self.active_pipeline
                else None,
                "fsm": self.to_dict(),
            }
        )

        await self._commit_updates_broadcaster.add_client(q)

    async def unsubscribe_from_commit_updates(self, q: asyncio.Queue):
        """Unsubscribe from updates from the cluster manager."""
        await self._commit_updates_broadcaster.remove_client(q)

    def has_shutdown(self) -> bool:
        """Check if the manager has shutdown."""
        return self._manager.has_shutdown

    def is_sentinel(self, msg: str):
        """Check if the message is a sentinel message."""
        if msg is self._network_updates_broadcaster._sentinel:
            return True
        elif msg is self._sentinel:
            return True
        else:
            return False

    async def activate_pipeline(
        self, pipeline_id: str
    ) -> Result[Pipeline, Union[str, Exception]]:
        """Activate the pipeline."""
        can, reason = self.can_transition("/activate")
        if not can:
            return Err(StateTransitionError(reason))

        pipeline = self._pipeline_service.get_pipeline(pipeline_id, throw=False)

        if pipeline is None:
            return Err(
                StateTransitionError(
                    f"Pipeline with id {pipeline_id} does not exist."
                )
            )

        if pipeline.doesnot_have_worker_mapping():
            return Err(
                StateTransitionError(
                    f"Pipeline {pipeline_id} does not have proper worker mapping."
                )
            )

        task = asyncio.create_task(self.instantiate_pipeline(pipeline))
        task.add_done_callback(
            lambda fut: self.transition_if_success(fut, "/activate")
        )

        if self.active_pipeline is not None:
            asyncio.create_task(self.destroy_pipeline(self.active_pipeline.id))

        self.active_pipeline = pipeline

        return Ok(pipeline)

    async def destroy_pipeline(self, active_pipeline_id):
        """Destroy the active pipeline."""
        pipeline = self._pipeline_service.get_pipeline(
            active_pipeline_id, throw=False
        )

        self._manager_busy = True
        if pipeline and pipeline.committed:
            await self._manager.async_reset(keep_workers=True)

        self._manager_busy = False

    def updater(self, pipeline_json=None):
        update_message = {
            "pipeline": pipeline_json or self.active_pipeline.to_web_json()
            if self.active_pipeline
            else None,
            "fsm": self.to_dict(),
        }

        asyncio.create_task(
            self._commit_updates_broadcaster.put_update(update_message)
        )

    async def committer(self, graph, worker_graph_mapping):
        self._manager_busy = True
        await self._manager.async_reset(keep_workers=True)
        self._manager_busy = False
        self._manager_busy = True
        await self._manager.async_commit(graph, worker_graph_mapping)
        self._manager_busy = False

    def transition_if_success(self, result, transition: str):
        print("Result exception", result.exception())
        if result.exception() is None:
            self.transitioning = False
            self.transition(transition)
            self.transitioning = False
            print("Transitioned to", transition, self.active_pipeline)
            self.updater()

    async def instantiate_pipeline(self, pipeline):
        """Instantiate the pipeline."""
        while self._manager_busy:
            await asyncio.sleep(0.1)

        self._manager_busy = True

        pipeline.instantiate(lambda msg: self.updater(msg))

    def assign_workers(
        self, pipeline_id: str, node_to_worker_ids: Dict[str, str]
    ) -> Result[Pipeline, Union[str, Exception]]:
        """Assign workers to the pipeline."""
        if self.transitioning:
            return Err(StateTransitionError("Cluster is transitioning."))

        pipeline = self._pipeline_service.get_pipeline(pipeline_id, throw=False)
        if pipeline is None:
            return Err(
                StateTransitionError(
                    f"Pipeline with id {pipeline_id} does not exist."
                )
            )

        if len(list(pipeline.nodes)) == 0:
            return Err(
                StateTransitionError(
                    f"Pipeline {pipeline_id} does not have any nodes."
                )
            )

        for _, data in pipeline.nodes(data=True):
            node = data["wrapped_node"]

            if node.id not in node_to_worker_ids:
                return Err(
                    StateTransitionError(
                        f"Node {node.name}/{node.id} does not have a valid worker id."
                    )
                )

            if node_to_worker_ids[node.id] is None:
                return Err(
                    StateTransitionError(
                        f"Node {node.name}/{node.id} does not have a valid worker id."
                    )
                )

            if node_to_worker_ids[node.id] not in self._manager.state.workers:
                return Err(
                    StateTransitionError(
                        f"Worker {node_to_worker_ids[node.id]} does not exist anymore."
                    )
                )

            node.worker_id = node_to_worker_ids[node.id]

        return Ok(pipeline)

    async def get_active_pipeline(
        self,
    ) -> Result[Pipeline, Union[str, Exception]]:
        """Get the active pipeline."""
        if self.active_pipeline is None:
            return Err(PipelineNotFoundError("No active pipeline."))

        return Ok(self.active_pipeline)

    async def commit(self) -> Result[Pipeline, Union[str, Exception]]:
        """Commit the active pipeline."""
        can, reason = self.can_transition("/commit")
        if not can:
            return Err(StateTransitionError(reason))

        if self.active_pipeline is None:
            return Err(StateTransitionError("No active pipeline."))

        if not self.active_pipeline.instantiated:
            return Err(StateTransitionError("Pipeline is not instantiated."))

        self.transitioning = True

        task = asyncio.create_task(
            self.active_pipeline.commit(
                updater=self.updater, committer=self.committer
            )
        )

        task.add_done_callback(
            lambda fut: self.transition_if_success(fut, "/commit")
        )

        return Ok(self.active_pipeline)

    async def preview(self):
        """Preview the active pipeline."""
        can, reason = self.can_transition("/preview")
        if not can:
            return Err(StateTransitionError(reason))

        if self.active_pipeline is None:
            return Err(StateTransitionError("No active pipeline."))

        if not self.active_pipeline.committed:
            return Err(StateTransitionError("Pipeline is not committed."))

        self.transitioning = True

        task = asyncio.create_task(self._manager.async_start())
        task.add_done_callback(
            lambda fut: self.transition_if_success(fut, "/preview")
        )

        return Ok(self.active_pipeline)

    async def record(self):
        """Record the active pipeline."""
        can, reason = self.can_transition("/record")
        if not can:
            return Err(StateTransitionError(reason))

        if self.active_pipeline is None:
            return Err(StateTransitionError("No active pipeline."))

        if not self.active_pipeline.committed:
            return Err(StateTransitionError("Pipeline is not committed."))

        self.transitioning = True

        task = asyncio.create_task(self._manager.async_record())
        task.add_done_callback(
            lambda fut: self.transition_if_success(fut, "/record")
        )

        return Ok(self.active_pipeline)

    async def stop(self):
        """Stop the active pipeline."""
        can, reason = self.can_transition("/stop")
        if not can:
            return Err(StateTransitionError(reason))

        if self.active_pipeline is None:
            return Err(StateTransitionError("No active pipeline."))

        self.transitioning = True

        task = asyncio.create_task(self._manager.async_stop())
        task.add_done_callback(
            lambda fut: self.transition_if_success(fut, "/stop")
        )

        return Ok(self.active_pipeline)

    async def reset(self) -> Result[Pipeline, Union[str, Exception]]:
        """Reset the active pipeline."""
        can, reason = self.can_transition("/reset")
        if not can:
            return Err(StateTransitionError(reason))

        if self.active_pipeline is None:
            return Err(StateTransitionError("No active pipeline."))

        self.transitioning = True

        task = asyncio.create_task(self._manager.async_reset(keep_workers=True))
        task.add_done_callback(lambda fut: self.signal_reset(fut))

        return Ok(self.active_pipeline)

    async def collect(self) -> Result[Pipeline, Union[str, Exception]]:
        """Collect the active pipeline."""
        can, reason = self.can_transition("/collect")
        if not can:
            return Err(StateTransitionError(reason))

        if self.active_pipeline is None:
            return Err(StateTransitionError("No active pipeline."))

        if not self.active_pipeline.committed:
            return Err(StateTransitionError("Pipeline is not committed."))

        self.transitioning = True

        task = asyncio.create_task(self._manager.async_collect())
        task.add_done_callback(
            lambda fut: self.transition_if_success(fut, "/collect")
        )

        return Ok(self.active_pipeline)

    def signal_reset(self, result):
        """Signal reset."""
        print("result", result.exception())
        if result.exception() is None:
            self.active_pipeline = None

        self.transition_if_success(result, "/reset")

    def get_states_info(self):
        """Return the FSM states info."""
        info = self.to_dict()
        return info
