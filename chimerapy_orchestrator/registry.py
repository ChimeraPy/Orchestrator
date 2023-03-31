from chimerapy_orchestrator.models.pipeline_models import WrappedNode


def get_registered_node(name: str) -> WrappedNode:
    """Returns a registered ChimeraPy Node as a WrappedNode."""
    from chimerapy_orchestrator import nodes_registry

    if name not in nodes_registry:
        raise ValueError(f"{name} is not registered as a ChimeraPy Node")
    return nodes_registry[name]
