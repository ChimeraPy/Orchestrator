import asyncio
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.websockets import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from chimerapy_orchestrator.models.cluster_models import (
    ClusterState,
    UpdateMessage,
    UpdateMessageType,
)
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
            "/zeroconf",
            self.toggle_zeroconf_discovery,
            methods=["POST"],
            response_description="Enable/Disable zeroconf discovery",
            description="Enable/Disable zeroconf discovery",
        )

        self.add_api_route(
            "/state",
            self.get_manager_state,
            methods=["GET"],
            response_description="The current state of the cluster",
            description="The current state of the cluster",
        )

        self.add_api_route(
            "/instantiate/{pipeline_id}",
            self.instantiate_pipeline,
            methods=["POST"],
            response_description="Instantiate a pipeline",
        )

        self.add_api_route(
            "/actions-fsm",
            self.get_actions_fsm,
            methods=["GET"],
            response_description="Get the actions FSM",
        )

        # FSM actions
        self.add_api_route(
            "/commit",
            self.commit,
            methods=["POST"],
            response_description="Commit the current pipeline in the cluster",
        )

        self.add_api_route(
            "/preview",
            self.preview,
            methods=["POST"],
            response_description="Preview the current pipeline in the cluster",
        )

        self.add_api_route(
            "/record",
            self.record,
            methods=["POST"],
            response_description="Record the current pipeline in the cluster",
        )

        self.add_api_route(
            "/stop",
            self.stop,
            methods=["POST"],
            response_description="Stop the current pipeline in the cluster",
        )

        self.add_api_route(
            "/reset",
            self.reset,
            methods=["POST"],
            response_description="Reset the current pipeline in the cluster",
        )

        # Websocket routes
        self.add_websocket_route("/cluster/updates", self.get_cluster_updates)
        self.add_websocket_route(
            "/cluster/pipeline-lifecycle", self.get_pipeline_updates
        )

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
                    self.manager.get_network().unwrap(),
                    zeroconf_discovery=self.manager.is_zeroconf_discovery_enabled(),
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

    async def get_pipeline_updates(self, websocket: WebSocket):
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

    async def get_manager_state(self) -> ClusterState:
        """Get the current state of the cluster."""
        return ClusterState.from_cp_manager_state(
            self.manager.get_network().unwrap(),
            zeroconf_discovery=self.manager.is_zeroconf_discovery_enabled(),
        )

    async def toggle_zeroconf_discovery(self, enable: bool) -> Dict[str, bool]:
        """Enable/Disable zeroconf discovery."""
        try:
            if enable:
                self.manager.enable_zeroconf_discovery()
            else:
                self.manager.disable_zeroconf_discovery()

            return {"success": True}

        except Exception as e:
            raise HTTPException(  # noqa: B904
                status_code=500,
                detail=f"Failed to toggle zeroconf discovery: {e}",
            )

    # Pipeline orchestration
    async def instantiate_pipeline(self, pipeline_id: str) -> bool:
        """Instantiate a pipeline."""
        result = await self.manager.instantiate_pipeline(pipeline_id)
        return result.map_error(
            lambda err: get_mapping(err).to_fastapi()
        ).unwrap()

    async def get_actions_fsm(self) -> Dict[str, Any]:
        """Get the actions FSM."""
        return self.manager.get_states_info()

    async def commit(self) -> bool:
        result = await self.manager.commit_pipeline()
        return result.map_error(
            lambda err: get_mapping(err).to_fastapi()
        ).unwrap()

    async def preview(self) -> bool:
        result = await self.manager.preview_pipeline()
        return result.map_error(
            lambda err: get_mapping(err).to_fastapi()
        ).unwrap()

    async def record(self) -> bool:
        result = await self.manager.record_pipeline()
        return result.map_error(
            lambda err: get_mapping(err).to_fastapi()
        ).unwrap()

    async def stop(self) -> bool:
        result = await self.manager.stop_pipeline()
        return result.map_error(
            lambda err: get_mapping(err).to_fastapi()
        ).unwrap()

    async def reset(self) -> bool:
        result = await self.manager.reset_pipeline()
        return result.map_error(
            lambda err: get_mapping(err).to_fastapi()
        ).unwrap()
