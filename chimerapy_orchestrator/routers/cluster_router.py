import asyncio
from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from chimerapy_orchestrator.models.cluster_models import (
    ClusterState,
    UpdateMessage,
    UpdateMessageType,
)
from chimerapy_orchestrator.models.pipeline_models import WebNode
from chimerapy_orchestrator.routers.error_mappers import get_mapping
from chimerapy_orchestrator.services.cluster_service import (
    ClusterManager,
)


async def relay(q: asyncio.Queue, ws: WebSocket, is_sentinel) -> None:
    """Relay messages from the queue to the websocket."""
    while True:
        message = await q.get()
        if ws.client_state == WebSocketState.DISCONNECTED:
            break
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
            "/activate-pipeline/{pipeline_id}",
            self.activate_pipeline,
            methods=["POST"],
            response_description="Activate a pipeline",
            description="Activate a pipeline",
        )

        self.add_api_route(
            "/commit",
            self.commit_route,
            methods=["POST"],
            response_description="Commit a pipeline to the cluster",
            description="Commit a pipeline to the cluster",
        )

        self.add_api_route(
            "/preview",
            self.preview_route,
            methods=["POST"],
            response_description="Preview a pipeline",
            description="Preview a pipeline",
        )

        self.add_api_route(
            "/record",
            self.record_route,
            methods=["POST"],
            response_description="Record a pipeline",
            description="Record a pipeline",
        )

        self.add_api_route(
            "/stop",
            self.stop_route,
            methods=["POST"],
            response_description="Stop a pipeline",
            description="Stop a pipeline",
        )

        self.add_api_route(
            "/reset",
            self.reset_route,
            methods=["POST"],
            response_description="Reset a pipeline",
            description="Reset a pipeline",
        )

        self.add_api_route(
            "/actions-fsm",
            self.get_actions_fsm,
            methods=["GET"],
            response_description="Get the actions FSM",
        )

        self.add_api_route(
            "/assign-workers/{pipeline_id}",
            self.assign_workers,
            methods=["POST"],
        )

        self.add_api_route(
            "/active-pipeline", self.get_active_pipeline, methods=["GET"]
        )

        # Websocket routes
        self.add_websocket_route(
            "/cluster/pipeline-lifecycle", self.get_pipeline_updates
        )
        self.add_websocket_route("/cluster/updates", self.get_cluster_updates)

    async def commit_route(self):
        """Commit a pipeline to the cluster."""
        pipeline = await self.manager.commit()

        return (
            pipeline.map(lambda p: p.to_web_json())
            .map_error(get_mapping)
            .unwrap()
        )

    async def preview_route(self):
        """Preview a pipeline."""
        pipeline = await self.manager.preview()

        return (
            pipeline.map(lambda p: p.to_web_json())
            .map_error(get_mapping)
            .unwrap()
        )

    async def record_route(self):
        """Record a pipeline."""
        pipeline = await self.manager.record()

        return (
            pipeline.map(lambda p: p.to_web_json())
            .map_error(get_mapping)
            .unwrap()
        )

    async def stop_route(self):
        """Stop a pipeline."""
        pipeline = await self.manager.stop()

        return (
            pipeline.map(lambda p: p.to_web_json())
            .map_error(get_mapping)
            .unwrap()
        )

    async def reset_route(self):
        pipeline = await self.manager.reset()

        return (
            pipeline.map(lambda p: p.to_web_json())
            .map_error(get_mapping)
            .unwrap()
        )

    async def assign_workers(
        self, pipeline_id: str, nodes: List[WebNode]
    ) -> Dict[str, Any]:
        """Assign workers to the given nodes."""
        node_to_worker_ids = {node.id: node.worker_id for node in nodes}

        return (
            self.manager.assign_workers(pipeline_id, node_to_worker_ids)
            .map(lambda pipeline: pipeline.to_web_json())
            .map_error(get_mapping)
            .unwrap()
        )

    async def get_manager_state(self) -> ClusterState:
        """Get the current state of the cluster."""
        return ClusterState.from_cp_manager_state(self.manager.get_network())

    async def activate_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Activate a pipeline."""
        result = await self.manager.activate_pipeline(pipeline_id)
        return (
            result.map(lambda p: p.to_web_json())
            .map_error(lambda err: get_mapping(err))
            .unwrap()
        )

    async def get_active_pipeline(self) -> Dict[str, Any]:
        """Get the active pipeline."""
        result = await self.manager.get_active_pipeline()
        return (
            result.map(lambda p: p.to_web_json())
            .map_error(lambda err: get_mapping(err))
            .unwrap()
        )

    async def get_actions_fsm(self) -> Dict[str, Any]:
        """Get the state of the cluster."""
        return self.manager.get_states_info()

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

    async def get_cluster_updates(self, websocket: WebSocket):  # noqa: C901
        """Get updates from the cluster manager and relay them to the client websocket."""
        await websocket.accept()

        update_queue = asyncio.Queue()
        relay_task = asyncio.create_task(
            relay(
                update_queue,
                websocket,
                lambda msg: self.manager.is_sentinel(msg),
            )
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
