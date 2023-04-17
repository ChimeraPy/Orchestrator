import json
from pathlib import Path
from typing import Dict, List

from chimerapy_orchestrator.network_service.network_manager import (
    NetworkManager,
)
from chimerapy_orchestrator.pipeline_service.pipeline import Pipeline
from chimerapy_orchestrator.state_machine.exceptions import StateTransitionError
from chimerapy_orchestrator.state_machine.fsm import FSM


class NetworkFSM(FSM):
    def __init__(self, manager: NetworkManager):
        self._initialize(manager)

    def _initialize(self, manager: NetworkManager):
        self.manager = manager
        self.current_state = self.initial_state

    async def commit(self, pipeline: Pipeline, mapping: Dict[str, List[str]]):
        try:
            self.transition("commit")
            pipeline.instantiate_graph()
            self.manager.commit_graph(pipeline, mapping)

        except StateTransitionError:
            pass

    @classmethod
    def __new__(cls, *args, **kwargs):
        with (Path(__file__).parent / "states.json").open("r") as f:
            states = json.load(f)

        return cls.from_dict(states)
