from typing import Optional

from chimerapy import Node

from chimerapy_orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)


def register_chimerapy_node(cls=None, *, name=None):
    if cls is not None:
        return RegistersChimeraPyNode(name)(cls)
    else:
        return RegistersChimeraPyNode(name)


class RegistersChimeraPyNode:
    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name

    def __call__(self, node_class: Node):
        if self.name is None:
            name = node_class.__name__
        else:
            name = self.name

        if name in ChimeraPyPipelineConfig.registered_nodes:
            raise ValueError(
                f"{name} is already registered as a ChimeraPy Node"
            )

        ChimeraPyPipelineConfig.registered_nodes[name] = node_class
        return node_class
