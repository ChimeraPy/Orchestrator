import json

import chimerapy as cp
import websockets
from chimerapy.networking.enums import GENERAL_MESSAGE

from chimerapy_orchestrator.utils import uuid


class NetworkManager(cp.Manager):
    def __init__(self, *args, **kwargs):
        kwargs["enable_api"] = True
        super().__init__(*args, **kwargs)

    async def connect_ws_client(
        self, socket: websockets.WebSocketClientProtocol
    ) -> None:
        await socket.send(
            json.dumps(
                {
                    "signal": GENERAL_MESSAGE.CLIENT_REGISTER.value,
                    "data": {"client_id": str(id(socket))},
                    "ok": True,
                    "uuid": uuid(),
                }
            )
        )
