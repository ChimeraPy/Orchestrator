import json
from typing import Any, Dict, List

import websockets
from chimerapy.networking.enums import GENERAL_MESSAGE
from chimerapy.utils import create_payload
from fastapi import APIRouter, BackgroundTasks, WebSocket

from chimerapy_orchestrator.network_service.network_manager import (
    NetworkManager,
)
from chimerapy_orchestrator.pipeline_service.pipelines import Pipelines


class NetworkRouter(APIRouter):
    def __init__(self, manager: NetworkManager, pipelines: Pipelines):
        super().__init__(prefix="/network", tags=["network_service"])
        self.manager = manager
        self.pipelines = pipelines
        self.add_api_route("/get", self.get_network, methods=["GET"])
        self.add_api_route("/commit", self.commit, methods=["POST"])
        self.add_websocket_route(
            "/network/ws", self.broadcast_network_updates, name="/network"
        )

    async def get_network(self) -> Dict[str, Any]:
        return self.manager.state.to_dict()

    async def commit(
        self,
        pipeline_id: str,
        mapping: Dict[str, List[str]],
        background_tasks: BackgroundTasks,
    ):
        background_tasks.add_task(self.manager.commit, pipeline_id, mapping)
        background_tasks.add_task(self.manager)

    async def broadcast_network_updates(self, socket: WebSocket):
        await socket.accept()
        async with websockets.connect(
            f"ws://{self.manager.host}:{self.manager.port}/ws"
        ) as client_ws:
            await self.manager.connect_ws_client(client_ws)
            while True:
                try:
                    changed_state = await client_ws.recv()
                    await socket.send_json(json.loads(changed_state))
                except websockets.exceptions.ConnectionClosedOK:
                    break
                except websockets.exceptions.ConnectionClosedError:
                    break

        await socket.close()

    async def send_connect_payload(self, socket: WebSocket):
        payload = create_payload(
            signal=GENERAL_MESSAGE.CLIENT_REGISTER,
            data={"client_id": str(id(socket))},
            ok=True,
        )
        await socket.send_json(payload)
