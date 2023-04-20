import asyncio
import json

import websockets
from fastapi import APIRouter
from fastapi.websockets import WebSocket, WebSocketDisconnect

from chimerapy_orchestrator.models.cluster_models import ClusterState
from chimerapy_orchestrator.services.cluster_service import (
    ClusterManager,
)


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
        client_ws = await self.manager.get_client_socket()

        await websocket.accept()
        await websocket.send_json(
            {
                "signal": self.manager.get_network_update_signal(),
                "data": ClusterState.from_cp_manager_state(
                    self.manager.get_network()
                ).dict(),
            }
        )

        while True:
            try:
                recv_task1 = asyncio.create_task(client_ws.recv())
                recv_task2 = asyncio.create_task(websocket.receive_json("text"))

                done, pending = await asyncio.wait(
                    [recv_task1, recv_task2],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                result = done.pop().result()
                msg = result if isinstance(result, dict) else json.loads(result)

                if self.manager.is_cluster_shutdown_message(msg):
                    await websocket.send_json({"signal": "shutdown"})
                    break

                if self.manager.is_cluster_update_message(msg):
                    updated = ClusterState.parse_obj(msg["data"]).dict()
                    await websocket.send_json(updated)

            except websockets.exceptions.ConnectionClosedOK:
                break
            except websockets.exceptions.ConnectionClosedError:
                break
            except WebSocketDisconnect:
                break

        await client_ws.close()
        await websocket.close()
