from setuptools import setup

setup(
    name="plugin-nodes-package",
    version="0.0.1",
    packages=["plugin_nodes_package"],
    install_requires=["chimerapy-orchestrator"],
    entry_points={
        "chimerapy.orchestrator.nodes_registry": {
            "get_nodes_registry = plugin_nodes_package:register_nodes_metadata"
        }
    },
)
