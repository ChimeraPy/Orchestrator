import typing
from typing import Dict

if typing.TYPE_CHECKING:
    from chimerapy_orchestrator.models.pipeline_models import WrappedNode

from collections import ChainMap

from chimerapy_orchestrator.models.registry_models import NodeType

source_nodes = {}  # noqa: F841
sink_nodes = {}  # noqa: F841
step_nodes = {}  # noqa: F841
nodes_registry = ChainMap(source_nodes, sink_nodes, step_nodes)  # noqa: F841


def get_registered_node(name: str) -> "WrappedNode":
    """Returns a registered ChimeraPy Node as a WrappedNode."""
    if name not in nodes_registry:
        raise ValueError(f"{name} is not registered as a ChimeraPy Node")
    return nodes_registry[name]


def all_nodes() -> Dict[str, "WrappedNode"]:
    """Returns all registered ChimeraPy Nodes."""
    return nodes_registry


def get_node_type(wrapped_node: "WrappedNode") -> NodeType:
    """Returns the type of a WrappedNode."""
    if wrapped_node.registry_name in source_nodes:
        return NodeType.SOURCE
    elif wrapped_node.registry_name in sink_nodes:
        return NodeType.SINK
    elif wrapped_node.registry_name in step_nodes:
        return NodeType.STEP
    else:
        raise ValueError(f"{wrapped_node} is not a registered ChimeraPy Node")
