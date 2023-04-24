import asyncio
import json
from typing import Any, Dict, Set

from chimerapy.networking.enums import GENERAL_MESSAGE, MANAGER_MESSAGE
from websockets import connect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from chimerapy_orchestrator.models.cluster_models import (
    UpdateMessage,
    UpdateMessageType,
)
from chimerapy_orchestrator.utils import uuid


class UpdatesBroadcaster:
    """A Queue based updates broadcaster

    Parameters
    ----------
    sentinel : str
        The sentinel message to stop the broadcaster.
    """

    def __init__(self, sentinel: str) -> None:
        self.update_queue = asyncio.Queue()
        self.sentinel = sentinel
        self.clients: Set[asyncio.Queue] = set()

    async def add_client(self, q: asyncio.Queue) -> None:
        """Add a client queue to the broadcaster."""
        self.clients.add(q)

    async def remove_client(self, q: asyncio.Queue) -> None:
        """Remove a client queue from the broadcaster."""
        self.clients.remove(q)

    async def put_update(self, msg: Dict[str, Any]) -> None:
        """Put an update message to the broadcaster."""
        self.update_queue.put_nowait(msg)

    async def start_broadcast(self) -> None:
        """Start the broadcaster."""
        while True:
            msg = await self.update_queue.get()
            if msg == self.sentinel:
                break
            for q in self.clients:
                q.put_nowait(msg)


class ClusterUpdatesBroadCaster:
    """A Queue based updates broadcaster from chimerapy manager to connected client queues.

    Parameters
    ----------
    host : str
        The host (ip address) of the cluster manager.

    port : int
        The port of the cluster manager.

    """

    _sentinel = "SHUTDOWN"

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.manager_update_socket = None
        self.clients: Set[asyncio.Queue] = set()

    async def initialize(self) -> None:
        """Initialize the update broadcaster."""
        self.manager_update_socket = await connect(
            f"ws://{self.host}:{self.port}/ws"
        )
        await self.manager_update_socket.send(
            json.dumps(self.connect_payload(str(id(self))))
        )

    async def add_client(
        self, q: asyncio.Queue, message: UpdateMessage = None
    ) -> None:
        """Add a client queue to the broadcaster."""
        if message is not None:
            await q.put(message.dict())
        self.clients.add(q)

    async def remove_client(self, q: asyncio.Queue) -> None:
        """Remove a client queue from the broadcaster."""
        self.clients.remove(q)

    async def enqueue_sentinel(self) -> None:
        """Enqueue a sentinel value to all client queues."""
        for q in self.clients:
            q.put_nowait(self._sentinel)

    async def broadcast_updates(self) -> None:
        """Broadcast updates to all clients."""
        while True:
            try:
                msg = await self.manager_update_socket.recv()
                msg = json.loads(msg)
                if self.is_cluster_update_message(msg):
                    msg = UpdateMessage.from_updates_dict(
                        msg, UpdateMessageType.NETWORK_UPDATE
                    )
                elif self.is_cluster_shutdown_message(msg):
                    msg = UpdateMessage.from_updates_dict(
                        msg, UpdateMessageType.SHUTDOWN
                    )
                else:
                    msg = None
                if msg is not None:
                    msg_dict = msg.dict()
                    for q in self.clients:
                        q.put_nowait(msg_dict)
                if msg and msg.signal is UpdateMessageType.SHUTDOWN:
                    break
            except ConnectionClosedOK:
                break
            except ConnectionClosedError:
                await self.enqueue_error()
                break

        await self.enqueue_sentinel()

    async def enqueue_error(self) -> None:
        """Enqueue an error message to all client queues."""
        for q in self.clients:
            q.put_nowait({"error": "Connection to manager lost."})

    @staticmethod
    def is_cluster_update_message(msg: Dict[str, Any]) -> bool:
        """Check if a message is a network update message."""
        return msg.get("signal") in [
            MANAGER_MESSAGE.NETWORK_STATUS_UPDATE.value,
            MANAGER_MESSAGE.NODE_STATUS_UPDATE.value,
        ]

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
