from fastapi import FastAPI

from chimerapy_orchestrator.cluster_service.cluster_manager import (
    ClusterManager,
)
from chimerapy_orchestrator.pipeline_service.pipelines import Pipelines
from chimerapy_orchestrator.routers.cluster_router import ClusterRouter
from chimerapy_orchestrator.routers.pipeline_router import PipelineRouter


class Orchestrator(FastAPI):
    def __init__(self, config):
        super().__init__()
        pipelines = Pipelines()
        cluster_manager = ClusterManager(
            logdir=config.cluster_manager_logdir,
            port=config.cluster_manager_port,
            max_num_of_workers=config.cluster_manager_max_num_of_workers,
        )

        self.include_router(PipelineRouter(pipelines))
        self.include_router(ClusterRouter(cluster_manager))


def create_orchestrator_app() -> "Orchestrator":
    from chimerapy_orchestrator.orchestrator_config import get_config

    orchestrator = Orchestrator(get_config())
    return orchestrator
