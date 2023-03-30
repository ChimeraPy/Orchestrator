import json
from pathlib import Path

import pytest

from chimerapy_orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)
from chimerapy_orchestrator.tests.base_test import BaseTest
from chimerapy_orchestrator.tests.utils import get_test_file_path


class TestPipelineConfig(BaseTest):
    @pytest.fixture(scope="class")
    def dummy_pipeline_config(self) -> ChimeraPyPipelineConfig:
        with get_test_file_path("dummy_pipeline.json").open() as f:
            return ChimeraPyPipelineConfig.parse_obj(json.load(f))

    def test_worker_config(self, dummy_pipeline_config):
        assert dummy_pipeline_config.workers.manager_ip == "localhost"
        assert dummy_pipeline_config.workers.manager_port == 8000

        assert dummy_pipeline_config.workers.instances[0].remote
        assert dummy_pipeline_config.workers.instances[0].name == "worker1"
        assert dummy_pipeline_config.workers.instances[0].id == "1235"

        assert not dummy_pipeline_config.workers.instances[1].remote
        assert dummy_pipeline_config.workers.instances[1].name == "worker2"
        assert dummy_pipeline_config.workers.instances[1].id == "1234"

        assert len(dummy_pipeline_config.workers.instances) == 2

    def test_nodes_config(self, dummy_pipeline_config):
        assert len(dummy_pipeline_config.nodes) == 2
        assert dummy_pipeline_config.nodes[0].name == "node1"
        assert dummy_pipeline_config.nodes[0].registry_name == "MyCustomNode"
        assert dummy_pipeline_config.nodes[0].kwargs == {
            "param1": 1,
            "param2": "abc",
        }
        assert dummy_pipeline_config.nodes[1].name == "node2"
        assert dummy_pipeline_config.nodes[1].registry_name == "node2"
        assert dummy_pipeline_config.nodes[1].kwargs == {}

    def test_adj_config(self, dummy_pipeline_config):
        assert len(dummy_pipeline_config.adj) == 1
        assert dummy_pipeline_config.adj[0] == ("node1", "node2")

    def test_mappings_config(self, dummy_pipeline_config):
        assert len(dummy_pipeline_config.mappings) == 2
        assert dummy_pipeline_config.mappings["worker1"] == ["node1"]
        assert dummy_pipeline_config.mappings["1234"] == ["node2"]

    def test_manager_config(self, dummy_pipeline_config):
        manager = dummy_pipeline_config.manager_config
        assert manager.port == 8000
        assert manager.logdir == Path("/tmp/logs")
