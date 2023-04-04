from typing import Dict

from chimerapy_orchestrator.models.pipeline_models import WrappedNode
from chimerapy_orchestrator.models.registry_models import NodeType


def get_registered_node(name: str) -> WrappedNode:
    """Returns a registered ChimeraPy Node as a WrappedNode."""
    from chimerapy_orchestrator import nodes_registry

    if name not in nodes_registry:
        raise ValueError(f"{name} is not registered as a ChimeraPy Node")
    return nodes_registry[name]


def all_nodes() -> Dict[str, WrappedNode]:
    """Returns all registered ChimeraPy Nodes."""
    from chimerapy_orchestrator import nodes_registry

    return nodes_registry


def get_node_type(wrapped_node: WrappedNode) -> NodeType:
    """Returns the type of a WrappedNode."""
    from chimerapy_orchestrator import sink_nodes, source_nodes, step_nodes

    if wrapped_node.NodeClass.__name__ in source_nodes:
        return NodeType.SOURCE
    elif wrapped_node.NodeClass.__name__ in sink_nodes:
        return NodeType.SINK
    elif wrapped_node.NodeClass.__name__ in step_nodes:
        return NodeType.STEP
    else:
        raise ValueError(f"{wrapped_node} is not a registered ChimeraPy Node")
