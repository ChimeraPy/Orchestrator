from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks

from chimerapy_orchestrator.network_service.network_manager import (
    NetworkManager,
)
from chimerapy_orchestrator.pipeline_service.pipelines import Pipelines


class NetworkRouter(APIRouter):
    def __init__(self, manager: NetworkManager, pipelines: Pipelines):
        super().__init__(prefix="/network", tags=["network_service"])
        self.manager = manager
        self.pipelines = pipelines
        self.add_api_route("/get", self.get_network, methods=["GET"])
        self.add_api_route("/commit", self.commit, methods=["POST"])

    async def get_network(self) -> Dict[str, Any]:
        return self.manager.state.to_dict()

    async def commit(
        self,
        pipeline_id: str,
        mapping: Dict[str, List[str]],
        background_tasks: BackgroundTasks,
    ):
        background_tasks.add_task(self.manager.commit, pipeline_id, mapping)
        background_tasks.add_task(self.manager)
