import json
import sys
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path

from chimerapy.engine.config import set
from chimerapy.orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)
from chimerapy.orchestrator.orchestrator_config import OrchestratorConfig


def orchestrate(config: ChimeraPyPipelineConfig):
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
    manager.commit_graph(graph=pipeline, mapping=mappings).result(
        timeout=config.timeouts.commit_timeout
    )

    if config.mode == "preview":
        manager.start().result(timeout=config.timeouts.preview_timeout)

    # Wait until user stops
    while True:
        q = input("Ready to start? (Y/n)")
        if q.lower() == "y":
            break

    manager.record().result(timeout=config.timeouts.record_timeout)

    # Wait until user stops
    if config.runtime is None:
        while True:
            q = input("Stop? (Y/n)")
            if q.lower() == "y":
                break
    else:  # Wait for runtime to elapse
        start_time = time.time()
        elapsed_time = time.time() - start_time
        while elapsed_time < config.runtime:
            elapsed_time = time.time() - start_time

    manager.stop().result(timeout=config.timeouts.stop_timeout)
    manager.collect().result(timeout=config.timeouts.collect_timeout)

    set("manager.timeout.worker-shutdown", config.timeouts.shutdown_timeout)
    manager.shutdown(blocking=True)


def orchestrate_worker(
    config: ChimeraPyPipelineConfig, worker_id: str, timeout=100
):
    worker = config.instantiate_remote_worker(worker_id)
    worker.connect(method="zeroconf", timeout=timeout)
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

    orchestrate_parser.add_argument(
        "--mode",
        help="Overwrite the mode from the config file",
        type=str,
        choices=["preview", "record"],
        required=False,
        default=None,
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
        help="The id of the worker in the config file",
        type=str,
        required=True,
    )

    orchestrate_worker_parser.add_argument(
        "--timeout",
        help="The timeout for the worker to connect",
        type=int,
        default=20,
        required=False,
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

    server_parser.add_argument(
        "--server-mode",
        help="The mode to run the server in",
        type=str,
        default="dev",
        choices=["dev", "prod"],
    )

    for field, model_field in OrchestratorConfig.model_fields.items():
        if field == "mode":
            continue

        server_parser.add_argument(
            f"--{field.replace('_', '-')}",
            help=model_field.description,
            type=model_field.annotation,
            required=False,
            default=model_field.default,
        )

    return server_parser


def run(args=None):
    parser = ArgumentParser(
        "The CP orchestrator", formatter_class=ArgumentDefaultsHelpFormatter
    )

    subparsers = parser.add_subparsers(
        title="subcommands", description="valid subcommands", dest="subcommand"
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

    if args.subcommand != "server":
        with open(args.config) as config_file:
            config_dict = json.load(config_file)
            cp_config = ChimeraPyPipelineConfig.model_validate(config_dict)

    if args.subcommand == "orchestrate":
        if args.mode and cp_config.mode != args.mode:
            cp_config.mode = args.mode
        orchestrate(cp_config)

    elif args.subcommand == "orchestrate-worker":
        orchestrate_worker(cp_config, args.worker_id, args.timeout)

    elif args.subcommand == "list-remote-workers":
        print("=== Remote Workers ===")
        cp_config.list_remote_workers()
        print("=== End Remote Workers ===")
    elif args.subcommand == "server":
        from uvicorn import run

        kwargs = {}
        for field in OrchestratorConfig.__fields__.keys():
            if field == "mode":
                continue

            if getattr(args, field) is not None:
                kwargs[field] = getattr(args, field)

        config = OrchestratorConfig(mode=args.server_mode, **kwargs)
        config.dump_env()
        run(
            "chimerapy.orchestrator.dashboard_app:create_orchestrator_app",
            port=args.server_port,
            factory=True,
            reload=True if args.server_mode == "dev" else False,
            lifespan="on",
            reload_dirs=[str(Path(__file__).parent.parent.resolve())],
        )

    else:
        parser.print_help()
