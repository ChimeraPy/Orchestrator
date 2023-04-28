import asyncio
import concurrent.futures
import signal
from contextlib import asynccontextmanager
from types import FrameType

from fastapi import FastAPI

from chimerapy_orchestrator.init_services import get, initialize, teardown
from chimerapy_orchestrator.routers.cluster_router import ClusterRouter
from chimerapy_orchestrator.routers.pipeline_router import PipelineRouter


@asynccontextmanager
async def lifespan(app: "Orchestrator"):
    default_sigint_handler = signal.getsignal(signal.SIGINT)
    cluster_service = get("cluster_manager")
    task1 = asyncio.create_task(cluster_service.start_async_tasks())

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
    with concurrent.futures.ThreadPoolExecutor() as pool:
        pool.submit(initialize)
    orchestrator = Orchestrator(lifespan=lifespan)
    return orchestrator
