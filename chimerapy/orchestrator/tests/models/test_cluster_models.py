from chimerapy.engine.states import (
    ManagerState as _ManagerState,
    WorkerState as _WorkerState,
    NodeState as _NodeState,
)

from chimerapy.orchestrator.models.cluster_models import (
    NodeState,
    WorkerState,
    ClusterState,
)

from pathlib import Path
from chimerapy.orchestrator.tests.base_test import BaseTest

import pytest


class TestClusterModels(BaseTest):
    @pytest.fixture(scope="class")
    def m_empty(self):
        return _ManagerState(
            id="manager1",
        )

    @pytest.fixture(scope="class")
    def m_populated(self):
        return _ManagerState(
            id="manager1",
            logdir=Path("/tmp24"),
            ip="192.168.2.0",
            port=55000,
            workers={},
            log_sink_enabled=True,
            logs_subscription_port=55001
        )

    @pytest.fixture(scope="class")
    def m_w_empty(self):
        return _ManagerState(
            id="manager1",
            logdir=Path("/tmp24"),
            ip="192.168.2.0",
            port=55000,
            log_sink_enabled=True,
            logs_subscription_port=55001,
            workers={
                "w1": _WorkerState(
                    id="w1",
                    name="worker1",
                    port=55002,
                    ip="192.168.2.1",
                    nodes={},
                    tempfolder=Path("/tmp24/w1")
                ),
                "w2": _WorkerState(
                    id="w2",
                    name="worker2",
                    port=55003,
                    ip="192.168.2.2",
                    nodes={},
                    tempfolder=Path("/tmp24/w2")
                )
            }
        )

    def test_m_empty(self, m_empty):
        manager_state = ClusterState.from_cp_manager_state(m_empty, zeroconf_discovery=False)
        assert manager_state.id == "manager1"
        assert manager_state.logdir == str(Path.cwd())
        assert manager_state.log_sink_enabled is False
        assert manager_state.logs_subscription_port is None
        assert manager_state.ip == "0.0.0.0"
        assert manager_state.port == 0
        assert manager_state.workers == {}

    def test_m_populated(self, m_populated):
        manager_state = ClusterState.from_cp_manager_state(m_populated, zeroconf_discovery=True)
        assert manager_state.id == "manager1"
        assert manager_state.logdir == "/tmp24"
        assert manager_state.log_sink_enabled is True
        assert manager_state.logs_subscription_port == 55001
        assert manager_state.ip == "192.168.2.0"
        assert manager_state.port == 55000
        assert manager_state.workers == {}
        assert manager_state.zeroconf_discovery is True

    def test_m_w_empty(self, m_w_empty):
        manager_state = ClusterState.from_cp_manager_state(m_w_empty, zeroconf_discovery=True)
        assert len(manager_state.workers) == 2
        w1 = manager_state.workers["w1"]
        assert w1.id == "w1"
        assert w1.name == "worker1"
        assert w1.port == 55002
        assert w1.ip == "192.168.2.1"
        assert w1.tempfolder == "/tmp24/w1"
        assert w1.nodes == {}
        assert isinstance(w1, WorkerState)

        w2 = manager_state.workers["w2"]
        assert w2.id == "w2"
        assert w2.name == "worker2"
        assert w2.port == 55003
        assert w2.ip == "192.168.2.2"
        assert w2.tempfolder == "/tmp24/w2"
        assert w2.nodes == {}
        assert isinstance(w2, WorkerState)


