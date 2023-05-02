def register_nodes_metadata():
    nodes = {
        "description": "Nodes from plugin-nodes-package",
        "nodes": [
            "plugin_nodes_package.registered_nodes:ANode",
            "plugin_nodes_package.registered_nodes:BNode",
        ],
    }

    return nodes
