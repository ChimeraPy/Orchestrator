import json
import sys
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from requests.exceptions import ConnectionError

from chimerapy_orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)


def orchestrate(config: ChimeraPyPipelineConfig):
    config.register_external_nodes()  # Register external nodes
    manager, pipeline, mappings, remote_workers = config.pipeline_graph()

    print("Waiting for remote workers to connect...")
    while True:
        if all(
            [
                remote_worker in manager.workers
                for remote_worker in remote_workers
            ]
        ):
            print("All remote workers connected!")
            break

    # Commit the graph
    manager.commit_graph(graph=pipeline, mapping=mappings)

    # Wail until user stops
    while True:
        q = input("Ready to start? (Y/n)")
        if q.lower() == "y":
            break

    manager.start()

    # Wail until user stops
    while True:
        q = input("Stop? (Y/n)")
        if q.lower() == "y":
            break

    manager.stop()
    manager.collect()
    manager.shutdown()


def orchestrate_worker(
    config: ChimeraPyPipelineConfig,
    worker_id: str,
    wait_until_connected=True,
    max_retries=10,
):
    worker = config.instantiate_remote_worker(worker_id)

    if wait_until_connected:
        for j in range(max_retries):
            if j == max_retries - 1:
                print("Max retries reached. Exiting...")
                sys.exit(1)
            try:
                worker.connect(
                    config.workers.manager_ip, config.workers.manager_port
                )
                break
            except ConnectionError:
                time.sleep(1)
                print(
                    f"Worker {worker_id} not connected yet. Waiting..., retries left: {max_retries - j - 1}"
                )
    else:
        try:
            worker.connect(
                config.workers.manager_ip, config.workers.manager_port
            )
        except ConnectionError:
            print(
                "Connection to manager failed. Please make sure the manager "
                "is running and the worker is connected to the same network."
            )
            sys.exit(1)

    print(f"Worker {worker_id} connected to manager!")
    worker.idle()

    worker.shutdown()


def add_orchestrate_parser(subparsers):
    # Orchestrate
    orchestrate_parser = subparsers.add_parser(
        "orchestrate",
        help="Orchestrate the pipeline",
    )

    orchestrate_parser.add_argument(
        "--config",
        help="The configuration file to use",
        type=str,
        required=True,
    )

    return orchestrate_parser


def add_orchestrate_worker_parser(subparsers):
    # Orchestrate worker
    orchestrate_worker_parser = subparsers.add_parser(
        "orchestrate-worker",
        help="Orchestrate a worker",
    )

    orchestrate_worker_parser.add_argument(
        "--config",
        help="The configuration file to use",
        type=str,
        required=True,
    )

    orchestrate_worker_parser.add_argument(
        "--worker-id",
        help="The id of the worker",
        type=str,
        required=True,
    )

    group = orchestrate_worker_parser.add_mutually_exclusive_group()
    group.add_argument(
        "--no-wait",
        help="Do not wait for the worker to connect to the manager",
        action="store_true",
    )

    group.add_argument(
        "--wait",
        help="Wait for the worker to connect to the manager",
        action="store_true",
    )

    return orchestrate_worker_parser


def add_list_remote_workers_parser(subparsers):
    # List remote workers
    list_remote_workers_parser = subparsers.add_parser(
        "list-remote-workers",
        help="List the remote workers",
    )

    list_remote_workers_parser.add_argument(
        "--config",
        help="The configuration file to use",
        type=str,
        required=True,
    )

    return list_remote_workers_parser


def add_server_parser(subparsers):
    # Server
    server_parser = subparsers.add_parser(
        "server",
        help="Start the server",
    )

    server_parser.add_argument(
        "--server-port",
        help="The port to run the server on",
        type=int,
        required="server" in sys.argv,
        default=8000,
    )


def run(args=None):
    parser = ArgumentParser(
        "The CP orchestrator", formatter_class=ArgumentDefaultsHelpFormatter
    )

    subparsers = parser.add_subparsers(
        title="subcommands", description="valid subcommands", dest="mode"
    )

    # Orchestrate
    add_orchestrate_parser(subparsers)

    # Orchestrate worker
    add_orchestrate_worker_parser(subparsers)

    # List remote workers
    add_list_remote_workers_parser(subparsers)

    # Server
    add_server_parser(subparsers)

    args = parser.parse_args(args)

    if args.mode != "server":
        with open(args.config) as config_file:
            config_dict = json.load(config_file)
            cp_config = ChimeraPyPipelineConfig.parse_obj(config_dict)

    if args.mode == "orchestrate":
        orchestrate(cp_config)
    elif args.mode == "orchestrate-worker":
        kwargs = {
            "wait_until_connected": not args.no_wait,
            "max_retries": args.max_retries,
        }
        orchestrate_worker(cp_config, args.worker_id, **kwargs)
    elif args.mode == "list-remote-workers":
        print("=== Remote Workers ===")
        cp_config.list_remote_workers()
        print("=== End Remote Workers ===")
    elif args.mode == "server":
        from uvicorn import run

        run(
            "chimerapy_orchestrator.orchestrator:create_orchestrator_app",
            port=args.server_port,
            factory=True,
            reload=True,
        )

    else:
        parser.print_help()
