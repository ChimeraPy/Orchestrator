import json
from typing import Any, Dict

import websockets
from chimerapy.manager import Manager
from chimerapy.networking.enums import GENERAL_MESSAGE, MANAGER_MESSAGE
from chimerapy.states import ManagerState

from chimerapy_orchestrator.services.pipeline_service import Pipelines
from chimerapy_orchestrator.utils import uuid


class ClusterManager:
    def __init__(self, pipeline_service: Pipelines, **manager_kwargs):
        """A service for managing the cluster manager."""
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

        self._pipeline_service = pipeline_service

        self.committed_pipeline = None

    def get_network(self) -> ManagerState:
        """Get the current state of the network."""
        return self._manager.state

    def shutdown(self):
        """Shutdown the cluster manager."""
        self._manager.shutdown()

    async def get_client_socket(self) -> websockets.WebSocketServerProtocol:
        """Register a socket as a client to the manager for listening to events like network changes."""
        socket = await websockets.connect(
            f"ws://{self._manager.host}:{self._manager.port}/ws"
        )

        payload = self.connect_payload(client_id=str(id(socket)))

        await socket.send(json.dumps(payload))

        return socket

    @property
    def host(self):
        return self._manager.host

    @property
    def port(self):
        return self._manager.port

    def has_shutdown(self) -> bool:
        """Check if the manager has shutdown."""
        return self._manager.has_shutdown

    def commit_pipeline(self, pipeline_id: str) -> None:
        """Commit a pipeline to the manager."""
        self._pipeline_service.get_pipeline(pipeline_id)

    @staticmethod
    def is_cluster_update_message(msg: Dict[str, Any]) -> bool:
        """Check if a message is a network update message."""
        return msg.get("signal") in [
            MANAGER_MESSAGE.NETWORK_STATUS_UPDATE.value,
            MANAGER_MESSAGE.NODE_STATUS_UPDATE.value,
        ]

    @staticmethod
    def get_network_update_signal() -> int:
        """Generate a network update message."""
        return MANAGER_MESSAGE.NETWORK_STATUS_UPDATE.value

    @staticmethod
    def is_cluster_shutdown_message(msg: Dict[str, Any]) -> bool:
        """Check if a message is a network shutdown message."""
        return msg.get("signal") == GENERAL_MESSAGE.SHUTDOWN.value

    @staticmethod
    def connect_payload(client_id: str) -> Dict[str, Any]:
        """Create a payload for registering a ws client to the manager."""
        return {
            "signal": GENERAL_MESSAGE.CLIENT_REGISTER.value,
            "data": {"client_id": client_id},
            "ok": True,
            "uuid": uuid(),
        }
