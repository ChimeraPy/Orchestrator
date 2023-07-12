import asyncio
import json
from typing import Any, Dict, Optional, Set

from websockets import connect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from chimerapy.engine.networking.enums import GENERAL_MESSAGE, MANAGER_MESSAGE
from chimerapy.orchestrator.models.cluster_models import (
    UpdateMessage,
    UpdateMessageType,
)
from chimerapy.orchestrator.utils import uuid


class UpdatesBroadcaster:
    """An asyncio.Queue based updates broadcaster.

    Parameters
    ----------
    sentinel: str
        The sentinel to be used to stop the broadcaster.
    """

    def __init__(self, sentinel: str = "SHUTDOWN"):
        self._sentinel = sentinel
        self._clients: Set[asyncio.Queue] = set()
        self.update_queue: Optional[asyncio.Queue] = None

    async def initialize(self) -> None:
        """Initialize the broadcaster."""
        self.update_queue = asyncio.Queue()

    async def add_client(self, q: asyncio.Queue) -> None:
        """Add a client queue to the broadcaster."""
        self._clients.add(q)

    async def remove_client(self, q: asyncio.Queue) -> None:
        """Remove a client queue from the broadcaster."""
        self._clients.remove(q)

    async def put_update(self, msg: Dict[str, Any]) -> None:
        """Put an update to the broadcaster."""
        if self.update_queue is None:
            await self.initialize()
        await self.update_queue.put(msg)

    def enqueue_sentinel(self) -> None:
        """Enqueue the sentinel message to stop the broadcaster."""
        self.update_queue.put_nowait(self._sentinel)

    async def start_broadcast(self) -> None:
        """Start the updates broadcaster"""
        if self.update_queue is None:
            await self.initialize()

        while True:
            msg = await self.update_queue.get()
            for q in self._clients:
                q.put_nowait(msg)
            if msg == self._sentinel:
                break


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
        self.updater = UpdatesBroadcaster(self._sentinel)
        self.updater_loop_task = None
        self.zeroconf_enabled = False

    def set_zeroconf_enabled(self, enabled: bool) -> None:
        """Set the zeroconf enabled flag."""
        self.zeroconf_enabled = enabled

    async def initialize(self) -> None:
        """Initialize the update broadcaster."""
        self.manager_update_socket = await connect(
            f"ws://{self.host}:{self.port}/ws"
        )
        await self.manager_update_socket.send(
            json.dumps(self.connect_payload(str(id(self))))
        )

        await self.updater.initialize()
        self.updater_loop_task = asyncio.create_task(
            self.updater.start_broadcast()
        )

    async def add_client(
        self, q: asyncio.Queue, message: UpdateMessage = None
    ) -> None:
        """Add a client queue to the broadcaster."""
        await self.updater.add_client(q)

        if message is not None:
            await q.put(message.dict())

    async def remove_client(self, q: asyncio.Queue) -> None:
        """Remove a client queue from the broadcaster."""
        await self.updater.remove_client(q)

    async def enqueue_sentinel(self) -> None:
        """Enqueue a sentinel value to all client queues."""
        self.updater.enqueue_sentinel()

    async def broadcast_updates(self) -> None:
        """Broadcast updates to all clients."""
        while True:
            try:
                msg = await self.manager_update_socket.recv()
                msg = json.loads(msg)
                if self.is_cluster_update_message(msg):
                    msg = UpdateMessage.from_updates_dict(
                        msg,
                        UpdateMessageType.NETWORK_UPDATE,
                        self.zeroconf_enabled,
                    )
                elif self.is_cluster_shutdown_message(msg):
                    msg = UpdateMessage.from_updates_dict(
                        msg, UpdateMessageType.SHUTDOWN, self.zeroconf_enabled
                    )
                else:
                    msg = None
                if msg is not None:
                    msg_dict = msg.dict()
                    await self.updater.put_update(msg_dict)
                if msg and msg.signal is UpdateMessageType.SHUTDOWN:
                    break
            except ConnectionClosedOK:
                break
            except ConnectionClosedError:
                await self.enqueue_error()
                break

        await self.enqueue_sentinel()

        if self.updater_loop_task is not None:
            self.updater_loop_task.cancel()

    async def enqueue_error(self) -> None:
        """Enqueue an error message to all client queues."""
        await self.updater.put_update({"error": "Connection to manager lost."})

    async def put_update(self, msg: Dict[str, Any]) -> None:
        """Put an update to the broadcaster."""
        update_msg = UpdateMessage.from_updates_dict(
            msg,
            UpdateMessageType.NETWORK_UPDATE,
            self.zeroconf_enabled,
        )
        await self.updater.put_update(update_msg.dict())

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
