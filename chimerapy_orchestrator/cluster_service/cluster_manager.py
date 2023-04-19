import json
from typing import Any, Dict

import websockets
from chimerapy.manager import Manager
from chimerapy.networking.enums import GENERAL_MESSAGE, MANAGER_MESSAGE
from chimerapy.states import ManagerState

from chimerapy_orchestrator.utils import uuid


class ClusterManager:
    def __init__(
        self,
        logdir: str,
        port: int = 9000,
        max_num_of_workers: int = 50,
        publish_logs_via_zmq: bool = False,
    ):
        self._manager = Manager(
            logdir=logdir,
            port=port,
            max_num_of_workers=max_num_of_workers,
            publish_logs_via_zmq=publish_logs_via_zmq,
            enable_api=True,
        )  # Here, we want to refactor this after we have a
        # better understanding of the Manager class into a duck-typed interface.

    def get_network(self) -> ManagerState:
        """Get the current state of the network."""
        return self._manager.state

    async def get_client_socket(self) -> websockets.WebSocketServerProtocol:
        """Register a socket as a client to the manager for listening to events like network changes."""
        socket = await websockets.connect(
            f"ws://{self._manager.host}:{self._manager.port}/ws"
        )

        payload = self.connect_payload(client_id=str(id(socket)))

        await socket.send(json.dumps(payload))

        return socket

    def is_cluster_update_message(self, msg: Dict[str, Any]) -> bool:
        """Check if a message is a network update message."""
        return msg.get("signal") in [
            MANAGER_MESSAGE.NETWORK_STATUS_UPDATE.value,
            MANAGER_MESSAGE.NODE_STATUS_UPDATE.value,
        ]

    @staticmethod
    def connect_payload(client_id):
        return {
            "signal": GENERAL_MESSAGE.CLIENT_REGISTER.value,
            "data": {"client_id": client_id},
            "ok": True,
            "uuid": uuid(),
        }
