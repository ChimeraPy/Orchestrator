import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.websockets import WebSocket, WebSocketDisconnect

from chimerapy_orchestrator.models.cluster_models import (
    ClusterState,
    UpdateMessage,
    UpdateMessageType,
)
from chimerapy_orchestrator.models.pipeline_models import WebNode
from chimerapy_orchestrator.services.cluster_service import (
    ClusterManager,
)


async def relay(q: asyncio.Queue, ws: WebSocket, is_sentinel) -> None:
    """Relay messages from the queue to the websocket."""
    while True:
        message = await q.get()
        if message is None:
            break
        if is_sentinel(message):  # Received Sentinel
            break
        try:
            await ws.send_json(message)
        except WebSocketDisconnect:
            break


async def poll(ws: WebSocket) -> None:
    """Continuously poll the websocket for messages."""
    while True:
        try:
            await ws.receive_json()  # FixMe: What is the best way of polling?
        except WebSocketDisconnect:
            break


class ClusterRouter(APIRouter):
    def __init__(self, manager: ClusterManager):
        super().__init__(prefix="/cluster", tags=["cluster_service"])
        self.manager = manager
        self.add_api_route(
            "/state",
            self.get_manager_state,
            methods=["GET"],
            response_description="The current state of the cluster",
            description="The current state of the cluster",
        )
        self.add_api_route(
            "/commit/{pipeline_id}",
            self.commit_pipeline,
            methods=["POST"],
            response_description="The current state of the committed pipeline",
            description="The current state of the committed pipeline",
        )
        self.add_websocket_route(
            "/cluster/committed-pipeline", self.get_pipeline_updates
        )
        self.add_websocket_route("/cluster/updates", self.get_cluster_updates)

    async def commit_pipeline(self, pipeline_id: str):
        """Commit a pipeline to the cluster."""
        can_commit, reason = await self.manager.can_commit()
        if not can_commit:
            print(f"Cannot commit pipeline: {reason}")
            raise HTTPException(
                status_code=403, detail=f"Cannot commit pipeline: {reason}"
            )

        pipeline = await self.manager.commit_pipeline(pipeline_id)

        return pipeline.to_web_json()

    async def get_pipeline_updates(self, websocket: WebSocket) -> None:
        await websocket.accept()

        update_queue = asyncio.Queue()
        relay_task = asyncio.create_task(
            relay(update_queue, websocket, self.manager.is_sentinel)
        )
        poll_task = asyncio.create_task(poll(websocket))
        await self.manager.subscribe_to_commit_updates(update_queue)
        try:
            done, pending = await asyncio.wait(
                [relay_task, poll_task], return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()

        finally:
            await self.manager.unsubscribe_from_commit_updates(update_queue)
            if not relay_task.done():
                relay_task.cancel()

    def assign_worker(self, pipeline_id: str, web_node: WebNode) -> WebNode:
        """Assign a worker to a pipeline."""
        self.manager.assign_worker(pipeline_id, web_node.id, web_node.worker_id)

    async def get_cluster_updates(self, websocket: WebSocket):  # noqa: C901
        """Get updates from the cluster manager and relay them to the client websocket."""
        await websocket.accept()

        update_queue = asyncio.Queue()
        relay_task = asyncio.create_task(
            relay(update_queue, websocket, self.manager.is_sentinel)
        )
        poll_task = asyncio.create_task(poll(websocket))
        await self.manager.subscribe_to_network_updates(
            update_queue,
            UpdateMessage(
                data=ClusterState.from_cp_manager_state(
                    self.manager.get_network()
                ),
                signal=UpdateMessageType.NETWORK_UPDATE,
            ),
        )
        try:
            done, pending = await asyncio.wait(
                [relay_task, poll_task], return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()

        finally:
            await self.manager.unsubscribe_from_network_updates(update_queue)
            if not relay_task.done():
                relay_task.cancel()

    async def get_manager_state(self) -> ClusterState:
        """Get the current state of the cluster."""
        return ClusterState.from_cp_manager_state(self.manager.get_network())
