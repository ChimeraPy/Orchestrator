import asyncio

import pytest

from chimerapy_orchestrator.services.cluster_service.updates_broadcaster import (
    UpdatesBroadcaster,
)
from chimerapy_orchestrator.tests.base_test import BaseTest


class TestUpdatesBroadCaster(BaseTest):
    @pytest.fixture(scope="class")
    def anyio_backend(self):
        return "asyncio"

    @pytest.fixture(scope="class")
    async def updates_broadcaster(self, anyio_backend):
        updates_broadcaster = UpdatesBroadcaster()
        await updates_broadcaster.initialize()
        update_task = asyncio.create_task(updates_broadcaster.start_broadcast())
        yield updates_broadcaster
        update_task.cancel()

    @pytest.mark.anyio
    async def test_update(self, updates_broadcaster):
        client_queue = asyncio.Queue()
        await updates_broadcaster.add_client(client_queue)
        for j in range(10):
            await updates_broadcaster.put_update(
                {
                    "message_type": "test",
                    "message_id": j,
                }
            )

        updates_broadcaster.enqueue_sentinel()

        for j in range(10):
            msg = await client_queue.get()
            assert msg["message_id"] == j
            assert msg["message_type"] == "test"
