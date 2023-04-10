from chimerapy_orchestrator.registry import (
    get_registered_node,
    sink_nodes,
    source_nodes,
)
from chimerapy_orchestrator.tests.base_test import BaseTest


class TestRegisteredNodes(BaseTest):
    def test_registered_nodes(self):
        assert get_registered_node("ScreenCaptureNode") is source_nodes.get(
            "ScreenCaptureNode"
        )
        assert get_registered_node("WebcamNode") is source_nodes.get(
            "WebcamNode"
        )

        assert get_registered_node("ShowWindow") is sink_nodes.get("ShowWindow")
