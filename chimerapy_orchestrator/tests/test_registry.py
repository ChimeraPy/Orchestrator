import pytest
from plugin_nodes_package.registered_nodes import ANode, BNode

from chimerapy_orchestrator.registry import (
    discovered_nodes,
    get_registered_node,
    importable_packages,
)
from chimerapy_orchestrator.tests.base_test import BaseTest
from chimerapy_orchestrator.tests.utils import can_find_plugin_nodes_package


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
        assert (
            get_registered_node("ANode", "plugin-nodes-package").NodeClass
            is ANode
        )

        assert (
            get_registered_node("BNode", "plugin-nodes-package").NodeClass
            is BNode
        )
