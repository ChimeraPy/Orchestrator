class StateTransitionError(ValueError):
    pass


class FSMFinishedError(StateTransitionError):
    pass
