from pathlib import Path

from chimerapy_orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)


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


def can_find_mmlapipe_configs():
    """Check if the mmlapipe package is installed."""
    found_mmlapipe_configs = True
    try:
        import mmlapipe  # noqa: F401

        mmlapipe_config_path = Path(mmlapipe.__file__).parent.parent / "configs"
        if not mmlapipe_config_path.exists():
            found_mmlapipe_configs = False
    except ImportError:
        found_mmlapipe_configs = False

    return found_mmlapipe_configs


def get_mmlapipe_configs_root_dir():
    """Get the root directory of the mmlapipe configs."""
    import mmlapipe  # noqa: F401

    return Path(mmlapipe.__file__).parent.parent / "configs"


def get_pipeline_config(pipeline, root_dir=None) -> ChimeraPyPipelineConfig:
    """Get a pipeline config from a pipeline name."""
    if root_dir is None:
        root_dir = Path(__file__).parent.parent.parent / "configs"

    config_path = root_dir.resolve() / f"{pipeline}.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Could not find config file {pipeline}")

    with config_path.open("r") as json_file:
        config = ChimeraPyPipelineConfig.parse_raw(json_file.read())

    return config
