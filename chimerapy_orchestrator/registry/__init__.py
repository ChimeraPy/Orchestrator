import importlib
import typing
import warnings
from typing import List, Tuple

import importlib_metadata

if typing.TYPE_CHECKING:
    from chimerapy_orchestrator.models.pipeline_models import WrappedNode

PACKAGE = "chimerapy-orchestrator"


class DiscoveredNodes:
    """A container for discovered nodes from plugins in ChimeraPyOrchestrator."""

    def __init__(self) -> None:
        self._nodes = {
            PACKAGE: {},
        }
        self._imported_nodes = []

    def add_node(
        self,
        name: str,
        node: "WrappedNode",
        package: str = None,
        add_to_default: bool = False,
    ) -> None:
        """Add a node to the registry."""

        if package is None and add_to_default:
            warnings.warn(
                "No package set, adding to default package",
                UserWarning,
                stacklevel=2,
            )
            package = PACKAGE

        if package is not None:
            if package not in self._nodes:
                self._nodes[package] = {}

            self._nodes[package][name] = node

    def add_imported_node(self, qualname: str, node: "WrappedNode") -> None:
        """Add a node that was imported from a package."""
        self._imported_nodes.append([qualname, node])

    def assign_package(self, package: str, qualname: str):
        """Assign a package to a node that was imported."""
        for qualname_, node in self._imported_nodes:
            if (
                qualname == qualname_
            ):  # FixME: There can be name collisions here? Package name collisions?
                node.package = package
                print(node.package)
                self.add_node(
                    node.registry_name, node, package, add_to_default=False
                )

    def get_node(self, name: str, package: str) -> "WrappedNode":
        """Get a node from the registry."""
        return self._nodes[package][name]

    def all_nodes(self):
        """A flat list of all registered nodes."""
        return [
            node
            for package in self._nodes.values()
            for node in package.values()
        ]

    def __contains__(self, package: str):
        """Check if a package is in the registry."""
        return package in self._nodes

    def remove_package(self, package: str):
        """Remove a package from the registry."""
        self._nodes.pop(package, None)


discovered_nodes = DiscoveredNodes()
plugin_registry = {}  # noqa: F841


def register_nodes_metadata() -> List[str]:
    """Register nodes from metadata."""
    nodes = [
        "chimerapy_orchestrator.registered_nodes.nodes:WebcamNode",
        "chimerapy_orchestrator.registered_nodes.nodes:ShowWindow",
        "chimerapy_orchestrator.registered_nodes.nodes:ScreenCaptureNode",
    ]

    return nodes


def load_registry_from_entrypoints() -> None:
    """Load the registry of importable registered nodes from entrypoints."""
    all_entry_points = importlib_metadata.entry_points().select(
        group="chimerapy_orchestrator.nodes_registry"
    )
    for entry_point in all_entry_points:
        if entry_point.name == "get_nodes_registry":
            package = entry_point.dist.metadata["Name"]
            plugin_registry[package] = entry_point.load()()


def check_registry(package: str) -> Tuple[bool, str]:
    """Check if a package is in the registry of importable registered nodes."""
    if package not in plugin_registry:
        return True, f"Package not found: {package}"

    for to_register_node in plugin_registry[package]:
        module, class_name = to_register_node.rsplit(":", 1)
        try:
            module = importlib.import_module(module)
            class_ = getattr(module, class_name)  # noqa: F841
            discovered_nodes.assign_package(package, to_register_node)
        except Exception as e:
            discovered_nodes.remove_package(package)
            return (
                True,
                f"Could not import all_nodes from {package}. Error: {e}",
            )

    return False, ""


def get_registered_node(name: str, package: str = None) -> "WrappedNode":
    """Returns a registered ChimeraPy Node as a WrappedNode."""
    if package is None:
        package = PACKAGE

    if package not in discovered_nodes:
        failure, reason = check_registry(package)
        if failure:
            raise ValueError(reason)
    try:
        return discovered_nodes.get_node(name, package)
    except KeyError as e:  # noqa: F841
        raise ValueError(f"Could not find node {name}.")  # noqa: B904


def all_nodes() -> List["WrappedNode"]:
    """Returns all registered ChimeraPy Nodes."""
    return discovered_nodes.all_nodes()


def importable_packages() -> List[str]:
    """Returns all the importable packages for ChimeraPy Nodes."""
    return list(
        filter(lambda x: x not in discovered_nodes, plugin_registry.keys())
    )


load_registry_from_entrypoints()
check_registry("chimerapy-orchestrator")
