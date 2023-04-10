from fastapi import FastAPI

from chimerapy_orchestrator.pipeline_service.pipelines import Pipelines
from chimerapy_orchestrator.routers.pipeline_router import PipelineRouter


class Orchestrator(FastAPI):
    def __init__(self):
        super().__init__()
        self.pipelines = Pipelines()
        self.include_router(PipelineRouter(self.pipelines))


def create_orchestrator_app() -> "Orchestrator":
    orchestrator = Orchestrator()
    return orchestrator
