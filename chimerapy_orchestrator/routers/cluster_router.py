import asyncio
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.websockets import WebSocket, WebSocketDisconnect

from chimerapy_orchestrator.models.cluster_models import (
    ClusterState,
    UpdateMessage,
    UpdateMessageType,
)
from chimerapy_orchestrator.services.cluster_service import (
    ClusterManager,
)


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

        self.add_websocket_route("/cluster/updates", self.get_cluster_updates)

    async def get_cluster_updates(self, websocket: WebSocket):  # noqa: C901
        """Get updates from the cluster manager and relay them to the client websocket."""
        await websocket.accept()

        async def relay(q: asyncio.Queue, ws: WebSocket) -> None:
            """Relay messages from the queue to the websocket."""
            while True:
                message = await q.get()
                if message is None:
                    break
                if self.manager.is_sentinel(message):  # Received Sentinel
                    break
                try:
                    await ws.send_json(message)
                except WebSocketDisconnect:
                    break

        async def on_disconnect() -> None:
            """Handle the disconnect of the client websocket."""
            await self.manager.unsubscribe_from_updates(update_queue)
            if not relay_task.cancelled():
                relay_task.cancel()

        async def poll(ws: WebSocket) -> None:
            """Continuously poll the websocket for messages."""
            while True:
                try:
                    await ws.receive_json()  # FixMe: What is the best way of polling?
                except WebSocketDisconnect:
                    break

        update_queue = asyncio.Queue()
        relay_task = asyncio.create_task(relay(update_queue, websocket))
        poll_task = asyncio.create_task(poll(websocket))
        await self.manager.subscribe_to_updates(
            update_queue,
            UpdateMessage(
                data=ClusterState.from_cp_manager_state(
                    self.manager.get_network(),
                    zeroconf_discovery=self.manager.is_discovery_enabled(),
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
            await on_disconnect()

    async def get_manager_state(self) -> ClusterState:
        """Get the current state of the cluster."""
        return ClusterState.from_cp_manager_state(
            self.manager.get_network(),
            zeroconf_discovery=self.manager.is_discovery_enabled(),
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
