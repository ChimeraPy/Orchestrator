from chimerapy_orchestrator.state_machine.fsm import StateTransitionError
from chimerapy_orchestrator.services.cluster_service.cluster_manager import PipelineNotFoundError
from fastapi.exceptions import HTTPException


def get_mapping(err):
    if isinstance(err, StateTransitionError):
        return HTTPException(status_code=403, detail=str(err))
    elif isinstance(err, PipelineNotFoundError):
        return HTTPException(status_code=404, detail=str(err))
    else:
        return HTTPException(status_code=500, detail=str(err))
