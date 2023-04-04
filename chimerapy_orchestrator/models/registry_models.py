from enum import Enum


class NodeType(str, Enum):
    """Enum for the different types of nodes."""

    SOURCE = "SOURCE"
    STEP = "STEP"
    SINK = "SINK"
