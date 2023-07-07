from fastapi.exceptions import HTTPException

from chimerapy_orchestrator.services.pipeline_service.pipeline import (
    EdgeNotFoundError,
    InvalidNodeError,
    NodeNotFoundError,
    NotADagError,
    PipelineInstantiationError,
)
from chimerapy_orchestrator.state_machine.exceptions import StateTransitionError


class CustomError:
    def __init__(self, status_code: int, msg: str):
        self.status_code = status_code
        self.msg = msg

    def to_fastapi(self):
        return HTTPException(
            status_code=self.status_code,
            detail=self.msg,
        )


def get_mapping(err: Exception) -> CustomError:
    """Maps an exception to a CustomError."""
    if isinstance(err, (EdgeNotFoundError, NodeNotFoundError)):
        return CustomError(404, str(err))
    elif isinstance(err, (InvalidNodeError, NotADagError)):
        return CustomError(500, str(err))
    elif isinstance(err, PipelineInstantiationError):
        return CustomError(400, str(err))
    elif isinstance(err, StateTransitionError):
        return CustomError(409, str(err))
    else:
        print(f"Unknown error: {err}")
        return CustomError(500, f"Internal server error {err}")
