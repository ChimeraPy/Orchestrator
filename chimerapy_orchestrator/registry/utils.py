from typing import Dict, Optional

from chimerapy import Node

from chimerapy_orchestrator.models.pipeline_models import WrappedNode


def source_node(cls=None, *, name=None):
    """Registers a source node."""
    from chimerapy_orchestrator.registry import source_nodes

    if cls is not None:
        return RegistersChimeraPyNode(name, source_nodes)(cls)
    else:
        return RegistersChimeraPyNode(name, source_nodes)


def sink_node(cls=None, *, name=None):
    """Register a sink node."""
    from chimerapy_orchestrator.registry import sink_nodes

    if cls is not None:
        return RegistersChimeraPyNode(name, sink_nodes)(cls)
    else:
        return RegistersChimeraPyNode(name, sink_nodes)


def step_node(cls=None, *, name=None):
    """Register a step node."""
    from chimerapy_orchestrator.registry import step_nodes

    if cls is not None:
        return RegistersChimeraPyNode(name, step_nodes)(cls)
    else:
        return RegistersChimeraPyNode(name, step_nodes)


class RegistersChimeraPyNode:
    """Registers a ChimeraPy Node."""

    def __init__(
        self, name: Optional[str], registry: Dict[str, WrappedNode]
    ) -> None:
        self.name = name
        self.registry = registry

    def __call__(self, node_class: Node):
        if not issubclass(node_class, Node):
            raise TypeError(f"{node_class} is not a ChimeraPy Node")

        if self.name is None:
            name = node_class.__name__
        else:
            name = self.name

        if name in self.registry:
            raise ValueError(
                f"{name} is already registered as a ChimeraPy Node"
            )

        wrapped_node = WrappedNode.from_node_class(node_class, registry_name=name)
        self.registry[name] = wrapped_node
        return node_class
