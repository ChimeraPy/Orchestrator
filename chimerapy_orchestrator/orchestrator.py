from fastapi import FastAPI

from chimerapy_orchestrator.network_service.network_manager import (
    NetworkManager,
)
from chimerapy_orchestrator.pipeline_service.pipelines import Pipelines
from chimerapy_orchestrator.routers.network_router import NetworkRouter
from chimerapy_orchestrator.routers.pipeline_router import PipelineRouter


class Orchestrator(FastAPI):
    def __init__(self):
        super().__init__()
        self.pipelines = Pipelines()
        self.network_manager = NetworkManager(
            logdir="?",
            port=5000,
        )
        print(self.network_manager.host, self.network_manager.port)
        self.include_router(NetworkRouter(self.network_manager))
        self.include_router(PipelineRouter(self.pipelines))


def create_orchestrator_app() -> "Orchestrator":
    orchestrator = Orchestrator()
    print("here")
    return orchestrator
