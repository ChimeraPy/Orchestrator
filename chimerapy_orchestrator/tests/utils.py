from pathlib import Path


def get_test_file_path(file_name: str) -> Path:
    """Get the path to a test file"""
    return Path(__file__).parent / "data" / file_name


def can_find_plugin_nodes_package():
    """Check if the plugin-nodes-package is installed."""
    found_plugin_nodes_package = True
    try:
        import plugin_nodes_package  # noqa: F401
    except ImportError:
        found_plugin_nodes_package = False

    return found_plugin_nodes_package
