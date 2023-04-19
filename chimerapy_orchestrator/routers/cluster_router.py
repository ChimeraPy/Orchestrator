import json

import websockets
from fastapi import APIRouter
from fastapi.websockets import WebSocket, WebSocketDisconnect

from chimerapy_orchestrator.cluster_service.cluster_manager import (
    ClusterManager,
)
from chimerapy_orchestrator.models.cluster_models import ClusterState


class ClusterRouter(APIRouter):
    def __init__(self, manager: ClusterManager):
        super().__init__(prefix="/cluster", tags=["cluster_service"])
        self.manager = manager
        self.add_api_route(
            "/state",
            self.get_state,
            methods=["GET"],
            response_description="The current state of the cluster",
            description="The current state of the cluster",
        )

        self.add_websocket_route("/cluster/updates", self.get_cluster_updates)

    async def get_state(self) -> ClusterState:
        return ClusterState.from_cp_manager_state(self.manager.get_network())

    async def get_cluster_updates(self, websocket: WebSocket):
        await websocket.accept()
        client_ws = await self.manager.get_client_socket()
        await websocket.send_json(
            ClusterState.from_cp_manager_state(
                self.manager.get_network()
            ).dict()
        )
        try:
            while True:
                try:
                    msg = json.loads(await client_ws.recv())
                    if self.manager.is_cluster_update_message(msg):
                        updated = ClusterState.parse_obj(msg["data"]).dict()
                        await websocket.send_json(updated)
                except websockets.exceptions.ConnectionClosedOk:
                    break
                except websockets.exceptions.ConnectionClosedError:
                    break
        except WebSocketDisconnect:
            await websocket.close()

        await client_ws.close()
