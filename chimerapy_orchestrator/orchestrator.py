import asyncio
import concurrent.futures
import signal
from contextlib import asynccontextmanager
from types import FrameType

from fastapi import FastAPI

from chimerapy_orchestrator.init_services import get, initialize, teardown
from chimerapy_orchestrator.routers.cluster_router import ClusterRouter
from chimerapy_orchestrator.routers.pipeline_router import PipelineRouter

APP_DESCRIPTION = """
REST API for managing the ChimeraPy cluster.

With this API, any client application can manage the cluster, including:
- Creating and managing pipelines for ChimeraPy
- Managing the cluster itself
- Running pipelines on the cluster

For more information, please visit the [documentation](https://chimerapy.readthedocs.io/en/latest/).
"""


@asynccontextmanager
async def lifespan(app: "Orchestrator"):
    default_sigint_handler = signal.getsignal(signal.SIGINT)
    cluster_service = get("cluster_manager")
    task1 = asyncio.create_task(cluster_service.start_async_tasks())
    await cluster_service.update_network_status()

    def shutdown():
        teardown()
        if not task1.done():
            task1.cancel()

    def shutdown_on_sigint(signum: int, frame: FrameType = None):
        shutdown()
        default_sigint_handler(signum, frame)

    signal.signal(signal.SIGINT, shutdown_on_sigint)
    yield
    shutdown()


class Orchestrator(FastAPI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        cluster_manager = get("cluster_manager")
        pipelines = get("pipelines")
        self.include_router(PipelineRouter(pipelines))
        self.include_router(ClusterRouter(cluster_manager))


def create_orchestrator_app() -> "Orchestrator":
    with concurrent.futures.ThreadPoolExecutor() as pool:  # This had to be done because uvicorn blocks the event loop
        pool.submit(initialize)

    orchestrator = Orchestrator(
        title="ChimeraPyOrchestrator",
        lifespan=lifespan,
        description=APP_DESCRIPTION,
        contact={
            "name": "Umesh Timalsina",
            "email": "umesh.timalsina@vanderbilt.edu",
        },
    )
    return orchestrator
