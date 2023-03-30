import json

import pytest

from chimerapy_orchestrator.state_machine.exceptions import (
    FSMFinishedError,
)
from chimerapy_orchestrator.state_machine.fsm import FSM
from chimerapy_orchestrator.tests.base_test import BaseTest
from chimerapy_orchestrator.tests.utils import get_test_file_path


class TestFSMModels(BaseTest):
    @pytest.fixture
    def push_pull_turnstile(self):
        with get_test_file_path(
            "example_fsms/push_pull_turnstile.json"
        ).open() as f:
            fsm_dict = json.load(f)
        return FSM.from_dict(fsm_dict)

    @pytest.fixture
    def workflow_fsm(self):
        with get_test_file_path("example_fsms/workflow.json").open() as f:
            fsm_dict = json.load(f)
        return FSM.from_dict(fsm_dict)

    def test_push_pull_turnstile(self, push_pull_turnstile):
        assert push_pull_turnstile.allowed_transitions == {"COIN", "PUSH"}

    def test_push_pull_turnstile_transitions(self, push_pull_turnstile):
        push_pull_turnstile.transition("COIN")
        assert push_pull_turnstile.allowed_transitions == {"PUSH", "COIN"}
        assert push_pull_turnstile.state == "UNLOCKED"

        push_pull_turnstile.transition("PUSH")
        assert push_pull_turnstile.allowed_transitions == {"COIN", "PUSH"}
        assert push_pull_turnstile.state == "LOCKED"

        push_pull_turnstile.transition("PUSH")
        assert push_pull_turnstile.allowed_transitions == {"COIN", "PUSH"}
        assert push_pull_turnstile.state == "LOCKED"

    def test_push_pull_turnstile_states(self, push_pull_turnstile):
        assert {state.name for state in push_pull_turnstile.states} == {
            "LOCKED",
            "UNLOCKED",
        }
        assert push_pull_turnstile.initial_state.name == "LOCKED"

    def test_workflow_fsm(self, workflow_fsm):
        assert workflow_fsm.allowed_transitions == {
            "UPDATE_DOCUMENT",
            "BEGIN_REVIEW",
        }
        assert workflow_fsm.state == "DRAFT"

        # Begin Reviewing
        workflow_fsm.transition("BEGIN_REVIEW")

        # Change Needed
        workflow_fsm.transition("CHANGE_NEEDED")

        # Reject Change
        workflow_fsm.transition("REJECT")

        assert workflow_fsm.state == "REVIEW"

        # Re Review and Request Change
        workflow_fsm.transition("CHANGE_NEEDED")

        # Accept Change
        workflow_fsm.transition("ACCEPT")

        assert workflow_fsm.state == "DRAFT"

        # Begin Reviewing
        workflow_fsm.transition("BEGIN_REVIEW")

        # Review Finished
        workflow_fsm.transition("SUBMIT")

        assert workflow_fsm.state == "SUBMITTED_TO_CLIENT"

        # Client Rejects
        workflow_fsm.transition("DECLINE")
        assert workflow_fsm.state == "DECLINED"

        # Rereview
        workflow_fsm.transition("RESTART_REVIEW")
        assert workflow_fsm.state == "REVIEW"

        # Request Change
        workflow_fsm.transition("CHANGE_NEEDED")
        assert workflow_fsm.state == "CHANGE_REQUESTED"

        # Accept Change
        workflow_fsm.transition("ACCEPT")
        assert workflow_fsm.state == "DRAFT"

        # Begin Reviewing
        workflow_fsm.transition("BEGIN_REVIEW")
        assert workflow_fsm.state == "REVIEW"

        # Review Finished
        workflow_fsm.transition("SUBMIT")
        assert workflow_fsm.state == "SUBMITTED_TO_CLIENT"

        # Client Approves
        workflow_fsm.transition("APPROVE")

        assert workflow_fsm.state == "APPROVED"
        assert workflow_fsm.is_finished

        with pytest.raises(FSMFinishedError):
            workflow_fsm.transition("APPROVE")
