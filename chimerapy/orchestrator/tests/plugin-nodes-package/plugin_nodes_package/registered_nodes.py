import chimerapy.engine as cpe
from chimerapy.orchestrator.registry.utils import sink_node, source_node


@source_node(name="ANode")
class ANode(cpe.Node):
    """A node that returns 5."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def step(self):
        return 5


@sink_node(name="BNode")
class BNode(cpe.Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def step(self, data_chunk):
        for name, data in data_chunk.items():
            print(f"{name}: {data}")
