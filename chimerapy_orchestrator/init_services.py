import chimerapy as cp

from chimerapy_orchestrator.orchestrator_config import get_config
from chimerapy_orchestrator.services.cluster_service import ClusterManager
from chimerapy_orchestrator.services.pipeline_service import Pipelines

available_services = {"cluster_manager": None, "pipelines": None, "workers": []}


def create_dev_worker(name):
    """Create a worker for development purposes."""
    worker = cp.Worker(name=name)
    worker.connect(method="zeroconf")
    return worker


def initialize():
    """Initialize the services. ToDo: Configure services via config file."""
    config = get_config()
    cluster_manager = ClusterManager(
        logdir=config.cluster_manager_logdir,
        port=config.cluster_manager_port,
        max_num_of_workers=config.cluster_manager_max_num_of_workers,
    )
    pipelines = Pipelines()
    available_services["cluster_manager"] = cluster_manager
    available_services["pipelines"] = pipelines
    if config.mode == "dev":

        for j in range(config.num_dev_workers):
            worker = create_dev_worker(f"DevWorker-{j+1}")
            available_services["workers"].append(worker)


def get(name):
    """Get a service by name."""
    if name not in available_services:
        raise ValueError(f"Service {name} is not available")
    return available_services[name]


def teardown():
    """Teardown the services."""
    manager = available_services.get("cluster_manager")
    if manager and not manager.has_shutdown():
        manager.shutdown()

    for worker in available_services.get("workers", []):
        if not worker.has_shutdown:
            worker.shutdown()
