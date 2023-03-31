from collections import ChainMap

source_nodes = {}  # noqa: F841
sink_nodes = {}  # noqa: F841
step_nodes = {}  # noqa: F841
nodes_registry = ChainMap(source_nodes, sink_nodes, step_nodes)  # noqa: F841


from . import registered_nodes
