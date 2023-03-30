from chimerapy_orchestrator.state_machine.models import State, Transition
from chimerapy_orchestrator.tests.base_test import BaseTest


class TestModels(BaseTest):
    def test_state(self):
        state = State(
            name="test_state",
            description="A test state",
            valid_transitions=[
                Transition(
                    name="test_transition",
                    from_state="test_state",
                    to_state="test_state2",
                )
            ],
        )
        assert state.name == "test_state"
        assert state.description == "A test state"
        assert state.valid_transitions[0].name == "test_transition"
        assert state.valid_transitions[0].from_state == "test_state"
        assert state.valid_transitions[0].to_state == "test_state2"
        assert len(state.valid_transitions) == 1
        assert state.describe() == f"test_state: A test state\n{repr(state)}"

    def test_transition(self):
        transition = Transition(
            name="test_transition",
            from_state="test_state",
            to_state="test_state2",
        )
        assert transition.name == "test_transition"
        assert transition.from_state == "test_state"
        assert transition.to_state == "test_state2"
        assert transition.key == "test_transition"
