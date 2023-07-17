import pytest

from chimerapy.orchestrator.models.pipeline_models import NodeType, WrappedNode
from chimerapy.orchestrator.registry import (
    DiscoveredNodes,
    discovered_nodes,
    get_registered_node,
    importable_packages,
)
from chimerapy.orchestrator.tests.base_test import BaseTest
from chimerapy.orchestrator.tests.utils import can_find_plugin_nodes_package


class TestRegisteredNodes(BaseTest):
    def test_registered_nodes(self):
        assert get_registered_node(
            "ScreenCaptureNode"
        ) is discovered_nodes.get_node(
            "ScreenCaptureNode", "chimerapy-orchestrator"
        )
        assert get_registered_node("WebcamNode") is discovered_nodes.get_node(
            "WebcamNode", "chimerapy-orchestrator"
        )

        assert get_registered_node("ShowWindow") is discovered_nodes.get_node(
            "ShowWindow", "chimerapy-orchestrator"
        )

    @pytest.mark.skipif(
        not can_find_plugin_nodes_package(),
        reason="plugin-nodes-package not found",
    )
    def test_plugin_nodes_packages_in_importable_packages(self):
        assert "plugin-nodes-package" in importable_packages()

    @pytest.mark.skipif(
        not can_find_plugin_nodes_package(),
        reason="plugin-nodes-package not found",
    )
    def test_plugin_nodes_package_nodes(self):
        from plugin_nodes_package.registered_nodes import ANode, BNode

        assert (
            get_registered_node("ANode", "plugin-nodes-package").NodeClass
            is ANode
        )

        assert (
            get_registered_node("BNode", "plugin-nodes-package").NodeClass
            is BNode
        )

    @pytest.mark.skipif(
        not can_find_plugin_nodes_package(),
        reason="plugin-nodes-package not found",
    )
    def test_discovered_nodes_implementation(self):
        from plugin_nodes_package.registered_nodes import ANode

        dnodes = DiscoveredNodes()
        assert dnodes._nodes["chimerapy-orchestrator"] == {}
        node = WrappedNode.from_node_class(ANode, NodeType.SOURCE, "NewNode")

        dnodes.add_node(
            "NewNode",
            node,
            package="chimerapy-orchestrator",
            add_to_default=False,
        )
        assert (
            dnodes.get_node("NewNode", "chimerapy-orchestrator").NodeClass
            is ANode
        )
        assert "chimerapy-orchestrator" in dnodes
