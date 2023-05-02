import pytest
from chimerapy.node import Node
from pydantic import ValidationError

from chimerapy_orchestrator.models.pipeline_models import (
    NodesPlugin,
    NodeType,
    WrappedNode,
)
from chimerapy_orchestrator.tests.base_test import BaseTest
from chimerapy_orchestrator.tests.utils import can_find_plugin_nodes_package


class TestPipelineModels(BaseTest):
    def test_non_node_instantiation_wrapped_node(self):
        with pytest.raises(ValidationError):
            WrappedNode.from_node_class(int, NodeType.SOURCE, "int")

    def test_node_instantiation_wrapped_node(self):
        class DummyNode(Node):
            def __init__(self, name="DummyNode", **kwargs):
                super().__init__(name=name, **kwargs)
                self.tunable_prop = None

            def prep(self):
                self.tunable_prop = 5

            def step(self):
                return self.tunable_prop

        wrapped_node = WrappedNode.from_node_class(
            DummyNode, node_type=NodeType.SOURCE, registry_name="DummyNode"
        )
        chimerapy_node = wrapped_node.instantiate()
        assert isinstance(chimerapy_node, DummyNode)
        assert chimerapy_node.name == "DummyNode"
        assert wrapped_node.instantiated
        assert wrapped_node.NodeClass.__name__ == "DummyNode"

    def test_wrapped_node_clone_and_web_node(self):
        class DummyNode(Node):
            def __init__(self, name="DummyNode", **kwargs):
                super().__init__(name=name, **kwargs)
                self.tunable_prop = None

            def prep(self):
                self.tunable_prop = 5

            def step(self):
                return self.tunable_prop

        wrapped_node = WrappedNode.from_node_class(
            DummyNode, node_type=NodeType.SOURCE, registry_name="DummyNode"
        )
        wrapped_node.instantiate()
        wrapped_node_clone = wrapped_node.clone()
        assert wrapped_node_clone.node_type == NodeType.SOURCE
        assert wrapped_node_clone.registry_name == "DummyNode"
        assert wrapped_node_clone.instantiated is False
        assert wrapped_node_clone.NodeClass == DummyNode
        assert wrapped_node_clone.to_web_node().dict() == {
            "name": "DummyNode",
            "registry_name": "DummyNode",
            "id": wrapped_node_clone.id,
            "kwargs": {},
            "type": NodeType.SOURCE,
            "package": None,
        }

    @pytest.mark.skipif(
        not can_find_plugin_nodes_package(),
        reason="plugin-nodes-package not found",
    )
    def test_nodes_plugin(self):
        plugin = NodesPlugin.from_plugin_registry("plugin-nodes-package")
        assert plugin.name == "plugin-nodes-package"
        assert plugin.package == "plugin-nodes-package"
        assert plugin.nodes == [
            "ANode",
            "BNode",
        ]
        assert plugin.version == "0.0.1"
        assert plugin.description == "Nodes from plugin-nodes-package"
