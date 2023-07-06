from typing import List, Optional, Union, Tuple

from chimerapy_orchestrator.state_machine.exceptions import (
    FSMFinishedError,
    StateTransitionError,
)
from chimerapy_orchestrator.state_machine.models import (
    State,
    Transition,
)


class FSM:
    """A finite state machine."""

    def __init__(
        self,
        states: List[State],
        initial_state: State,
        description: Optional[str] = None,
    ):
        self.states = states
        self.initial_state = initial_state
        self.current_state = initial_state
        self.description = description or "A finite state machine."
        final_states = set()

        for state in states:
            if (
                state.valid_transitions is None
                or len(state.valid_transitions) == 0
            ):
                final_states.add(state)

        self.final_states = frozenset(final_states)
        self.transitioning = False
        self.valid_transitions_names = self._collect_state_and_transitions()

    def _collect_state_and_transitions(self):
        transitions = set()
        for state in self.states:
            for transition in state.valid_transitions:
                if transition.to_state not in self.state_names:
                    raise ValueError(
                        f"Transition {transition} is invalid. State {transition.to_state} does not exist."
                    )
                transitions.add(transition.name)
        return transitions

    @property
    def state_names(self):
        return {s.name for s in self.states}

    @property
    def transition_names(self):
        return self.valid_transitions_names

    @property
    def state(self):
        return self.current_state.name

    @property
    def allowed_transitions(self):
        return {t.key for t in self.current_state.valid_transitions}

    def transition(self, transition: Union[Transition, str]) -> None:
        """Transition to a new state."""
        self.transitioning = True
        if self.transitioning:
            raise StateTransitionError("Cannot transition while transitioning")

        if self.is_finished:
            raise FSMFinishedError("The final state reached")

        # If the transition is a string, get the transition object
        if isinstance(transition, str):
            if transition not in self.transition_names:
                raise StateTransitionError(f"Invalid transition: {transition}")

            tmp = transition

            tmp = self.get_current_state_transition(tmp)

            if tmp is None:
                tmp = self.get_transition(transition)
                if tmp is not None:
                    raise StateTransitionError(
                        f"Invalid transition: {transition} from state {self.current_state.name} is not possible"
                    )
                else:
                    raise StateTransitionError(
                        f"Invalid transition: {transition}"
                    )
            else:
                transition = tmp

        self.current_state = self._get_state_from_transition(transition)
        self.transitioning = False

    def _get_state_from_transition(self, transition: Transition) -> State:
        for state in self.states:
            if state.name == transition.to_state:
                return state

    def is_valid_transition(self, transition: Transition) -> bool:
        if transition is None:
            return False

        return transition in self.current_state.valid_transitions

    def get_current_state_transition(
        self, transition_name: str
    ) -> Optional[Transition]:
        # Check if the transition is valid in the current state
        for transition in self.current_state.valid_transitions:
            if transition.name == transition_name:
                return transition

    def can_transition(self, transition_name) -> Tuple[bool, str]:
        if self.transitioning:
            return False, "Cannot transition while transitioning"
        if transition_name in self.allowed_transitions:
            return True, ""
        else:
            return False, f"Invalid transition: {transition_name} from state {self.current_state.name} is not possible"

    def get_transition(self, transition_name: str) -> Optional[Transition]:
        # Check if the transition is valid in any state
        for state in self.states:
            for transition in state.valid_transitions:
                if transition.name == transition_name:
                    return transition

    def to_dict(self):
        return {
            "current_state": self.current_state.name,
            "description": self.description,
            "initial_state": self.initial_state.name,
            "states": {state.name: state.dict() for state in self.states},
        }

    @property
    def is_finished(self):
        return self.current_state in self.final_states

    def __repr__(self):
        return f"<FSM {self.current_state.name}>"

    @staticmethod
    def parse_dict(dict_obj):
        state_cache = {}
        for state_name, props in dict_obj["states"].items():
            state_cache[state_name] = State(
                name=state_name,
                valid_transitions=[
                    Transition.parse_obj(t_dict)
                    for t_dict in props["valid_transitions"]
                ],
                description=props["description"],
            )

        return state_cache, state_cache[dict_obj["initial_state"]]

    @classmethod
    def from_dict(cls, dict_obj):
        state_cache, initial_state = cls.parse_dict(dict_obj)

        return cls(
            states=list(state_cache.values()),
            initial_state=state_cache[dict_obj["initial_state"]],
            description=dict_obj["description"],
        )
