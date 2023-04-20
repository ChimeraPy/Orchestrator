import signal
from contextlib import asynccontextmanager
from types import FrameType

from fastapi import FastAPI

from chimerapy_orchestrator.routers.cluster_router import ClusterRouter
from chimerapy_orchestrator.routers.pipeline_router import PipelineRouter
from chimerapy_orchestrator.services.cluster_service import (
    ClusterManager,
)
from chimerapy_orchestrator.services.pipeline_service import Pipelines


@asynccontextmanager
async def lifespan(app: "Orchestrator"):
    default_sigint_handler = signal.getsignal(signal.SIGINT)

    def shutdown_on_sigint(signum: int, frame: FrameType = None):
        app.cluster_manager.shutdown()
        default_sigint_handler(signum, frame)

    signal.signal(signal.SIGINT, shutdown_on_sigint)

    yield

    if not app.cluster_manager.has_shutdown():
        app.cluster_manager.shutdown()


class Orchestrator(FastAPI):
    def __init__(self, config, **kwargs):
        super().__init__(**kwargs)

        # Services
        self.pipelines = Pipelines()
        self.cluster_manager = ClusterManager(
            logdir=config.cluster_manager_logdir,
            port=config.cluster_manager_port,
            max_num_of_workers=config.cluster_manager_max_num_of_workers,
        )

        # Routers
        self.include_router(PipelineRouter(self.pipelines))
        self.include_router(ClusterRouter(self.cluster_manager))


def create_orchestrator_app() -> "Orchestrator":
    from chimerapy_orchestrator.orchestrator_config import get_config

    orchestrator = Orchestrator(get_config(), lifespan=lifespan)
    return orchestrator
