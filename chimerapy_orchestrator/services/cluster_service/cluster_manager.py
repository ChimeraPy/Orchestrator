import asyncio
from typing import Any, Dict, List, Tuple

import networkx as nx
from chimerapy.manager import Manager
from chimerapy.states import ManagerState

from chimerapy_orchestrator.models.cluster_models import UpdateMessage
from chimerapy_orchestrator.services.cluster_service.updates_broadcaster import (
    ClusterUpdatesBroadCaster,
    UpdatesBroadcaster,
)
from chimerapy_orchestrator.services.pipeline_service import Pipeline, Pipelines


class ClusterManager:
    def __init__(self, pipeline_service: Pipelines, **manager_kwargs):
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
        self.committed_pipeline = None

    @property
    def host(self):
        return self._manager.host

    @property
    def port(self):
        return self._manager.port

    def get_network(self) -> ManagerState:
        """Get the current state of the network."""
        return self._manager.state

    async def start_updates_broadcaster(self):
        """Begin the updates broadcaster."""
        await self._network_updates_broadcaster.initialize()
        asyncio.create_task(
            self._network_updates_broadcaster.broadcast_updates()
        )
        asyncio.create_task(self._commit_updates_broadcaster.start_broadcast())

    def shutdown(self):
        """Shutdown the cluster manager."""
        asyncio.ensure_future(
            self._commit_updates_broadcaster.put_update(self._sentinel)
        )
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
        await self._commit_updates_broadcaster.add_client(q)

    async def unsubscribe_from_commit_updates(self, q: asyncio.Queue):
        """Unsubscribe from updates from the cluster manager."""
        await self._commit_updates_broadcaster.remove_client(q)

    def has_shutdown(self) -> bool:
        """Check if the manager has shutdown."""
        return self._manager.has_shutdown

    def is_sentinel(self, msg: str):
        """Check if the message is a sentinel message."""
        return msg == self._network_updates_broadcaster._sentinel

    async def commit_pipeline(self, pipeline_id: str) -> Pipeline:
        """Commit a pipeline."""
        if self.committed_pipeline:
            raise ValueError("A pipeline is already committed.")

        pipeline = self._pipeline_service.get_pipeline(pipeline_id)

        asyncio.create_task(self._commit_pipeline(pipeline))

        return pipeline

    async def _commit_pipeline(self, pipeline: Pipeline) -> None:
        async def update_pipeline_commit_state(msg: Dict[str, Any]) -> None:
            msg["state"] = "Instantiating Nodes"
            await self._commit_updates_broadcaster.put_update(msg)

        async def commit_pipeline(
            graph: nx.DiGraph, worker_graph_mapping: Dict[str, List[str]]
        ):
            self._manager.commit_graph(graph, worker_graph_mapping)

        await pipeline.instantiate_and_commit(
            update_pipeline_commit_state, commit_pipeline
        )
        pipeline.assign_commit_success()
        await update_pipeline_commit_state(pipeline.assign_commit_success())

    async def assign_worker(
        self, pipeline_id: str, node_id: str, worker_id: str
    ) -> "WrappedNode":
        """Assign worker to a pipeline node."""
        pipeline = self._pipeline_service.get_pipeline(pipeline_id)

        await pipeline.assign_worker(node_id, worker_id)

        return pipeline.nodes[node_id]["wrapped_node"]

    async def can_commit(self, pipeline_id: str) -> Tuple[bool, str]:
        """Check if we can commit a pipeline."""
        pipeline = self._pipeline_service.get_pipeline(pipeline_id, throw=False)

        if pipeline is None:
            return False, f"Pipeline {pipeline_id} does not exist."

        if self.committed_pipeline:
            return False, "A pipeline is already committed."

        if len(self._manager.state.workers) == 0:
            return False, "No workers are available."

        for _, data in pipeline.nodes(data=True):
            wrapped_node = data["wrapped_node"]
            if wrapped_node.worker_id is None:
                return False, f"All nodes are not assigned a worker"
            if wrapped_node.worker_id not in self._manager.state.workers:
                return False, f"Worker {wrapped_node.worker_id} is not available"

        if len(pipeline.nodes) == 0:
            return False, "Pipeline has no nodes."

        return True, "Pipeline can be committed."
