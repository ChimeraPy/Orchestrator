import pytest
from chimerapy.node import Node
from pydantic import ValidationError

from chimerapy_orchestrator.models.pipeline_models import WrappedNode
from chimerapy_orchestrator.tests.base_test import BaseTest


class TestPipelineModels(BaseTest):
    def test_non_node_instantiation_wrapped_node(self):
        with pytest.raises(ValidationError):
            WrappedNode.from_node_class(int)

    def test_node_instantiation_wrapped_node(self):
        class DummyNode(Node):
            def __init__(self):
                super().__init__()
                self.tunable_prop = None

            def prep(self):
                self.tunable_prop = 5

            def step(self):
                return self.tunable_prop

        wrapped_node = WrappedNode.from_node_class(DummyNode)
        assert wrapped_node.NodeClass.__name__ == "DummyNode"
