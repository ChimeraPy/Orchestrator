
import asyncio
from typing import Union


class AsyncTask:
    def __init__(self, coro, kwargs, done_callback):
        self.coro = coro
        self.kwargs = kwargs
        self.done_callback = done_callback


class AsyncTaskQueue:
    def __init__(self, sentinel=None):
        self._queue = None
        self.current_task = None
        self._sentinel = sentinel
        self.loop_task = None

    async def initialize(self):
        self._queue = asyncio.Queue()
        self.loop_task = asyncio.create_task(self.task_loop())

    async def add_task(self, async_task: Union[AsyncTask,  None]):
        self._queue.put_nowait(async_task)

    async def cancel(self):
        if not self.current_task.done():
            self.current_task.cancel()

    async def enqueue_sentinel(self):
        await self._queue.put_nowait(self._sentinel)

    async def task_loop(self):
        while True:
            task: AsyncTask = await self._queue.get()
            if task is self._sentinel:
                break
            print("Running task: ", task.coro.__name__)

            created_task = asyncio.ensure_future(task.coro(**task.kwargs))
            created_task.add_done_callback(task.done_callback)

            self.current_task = created_task

            while not self.current_task.done():
                print("Waiting for task to finish")
                continue

            self._queue.task_done()

    async def shutdown(self):

        await self.cancel()

        if not self._queue.empty():
            self._queue.clear()

        await self.enqueue_sentinel()
