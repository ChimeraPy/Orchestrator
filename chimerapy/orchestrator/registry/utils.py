import inspect
from typing import Any, Dict, Optional, Type

from chimerapy.engine import Node
from chimerapy.orchestrator.models.pipeline_models import NodeType, WrappedNode


def source_node(cls=None, *, name=None, add_to_registry=False):
    """Registers a source node."""
    if cls is not None:
        return RegistersChimeraPyNode(
            name, NodeType.SOURCE, add_to_registry=add_to_registry
        )(cls)
    else:
        return RegistersChimeraPyNode(
            name, NodeType.SOURCE, add_to_registry=add_to_registry
        )


def sink_node(cls=None, *, name=None, add_to_registry=False):
    """Register a sink node."""

    if cls is not None:
        return RegistersChimeraPyNode(
            name, NodeType.SINK, add_to_registry=add_to_registry
        )(cls)
    else:
        return RegistersChimeraPyNode(
            name, NodeType.SINK, add_to_registry=add_to_registry
        )


def step_node(cls=None, *, name=None, add_to_registry=False):
    """Register a step node."""

    if cls is not None:
        return RegistersChimeraPyNode(
            name, NodeType.STEP, add_to_registry=add_to_registry
        )(cls)
    else:
        return RegistersChimeraPyNode(
            name, NodeType.STEP, add_to_registry=add_to_registry
        )


class RegistersChimeraPyNode:
    """Registers a ChimeraPy Node."""

    def __init__(
        self,
        name: Optional[str],
        node_type: NodeType,
        add_to_registry: bool = False,
    ) -> None:
        self.name = name
        self.type = node_type
        self.add_to_registry = add_to_registry

    def __call__(self, node_class: Type[Node]):
        from chimerapy.orchestrator.registry import discovered_nodes

        if not issubclass(node_class, Node):
            raise TypeError(f"{node_class} is not a ChimeraPy Node")

        if self.name is None:
            name = node_class.__name__
        else:
            name = self.name

        wrapped_node = WrappedNode.from_node_class(
            node_class,
            node_type=self.type,
            registry_name=name,
            kwargs=self._parse_init_kwargs(node_class),
        )

        qualified_name = f"{node_class.__module__}:{node_class.__name__}"

        discovered_nodes.add_imported_node(qualified_name, wrapped_node)

        if self.add_to_registry:
            discovered_nodes.add_node(
                wrapped_node.registry_name, wrapped_node, add_to_default=True
            )

        return node_class

    def _parse_init_kwargs(self, node_class: Type[Node]) -> Dict[str, Any]:
        signature = inspect.signature(node_class.__init__)
        kwargs = {}

        for param in signature.parameters.values():

            if param.name == "self":
                continue
            kwargs[param.name] = (
                param.default if param.default is not param.empty else None
            )

        return kwargs
