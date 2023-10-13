import asyncio
import json
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path
from typing import Dict, Iterable, List, Set

import tqdm

from chimerapy.engine import Manager, Worker
from chimerapy.engine import config as cpe_config
from chimerapy.engine.utils import async_waiting_for
from chimerapy.orchestrator.models.pipeline_config import (
    ChimeraPyPipelineConfig,
)
from chimerapy.orchestrator.orchestrator_config import OrchestratorConfig


def _check_remote_workers(manager: Manager, remote_workers: Iterable[str]):
    return all(
        [remote_worker in manager.workers for remote_worker in remote_workers]
    )


async def _connect_workers(
    manager: Manager, config: ChimeraPyPipelineConfig
) -> Set[Worker]:
    # Create Local Workers and Connect
    remote_workers = set()
    local_workers = set()
    for wc in config.workers.instances:
        if not wc.remote:
            w = Worker(name=wc.name, id=wc.id, port=0, delete_temp=True)
            await w.aserve()
            await w.async_connect(method="zeroconf", timeout=20)
            local_workers.add(w)
        else:
            remote_workers.add(wc.id)

    # Wait until workers connect
    print("Waiting for workers to connect...")
    await async_waiting_for(
        lambda: _check_remote_workers(manager, remote_workers),
    )
    print("All remote workers connected!")
    return local_workers


def _get_mappings(
    config: ChimeraPyPipelineConfig, created_nodes: Dict
) -> Dict[str, List[str]]:
    mp = {}
    for worker_id in config.mappings:
        if mp.get(worker_id) is None:
            mp[worker_id] = []

        for node_name in config.mappings[worker_id]:
            mp[worker_id].append(created_nodes[node_name].id)
    return mp


async def _pipeline_preview(manager: Manager) -> None:
    await manager.async_start()

    # Wait until user stops
    while True:
        q = input("Ready to start? (Y/n)")
        if q.lower() == "y":
            break

    await manager.async_record()


async def _pipeline_record(manager: Manager) -> None:
    while True:
        q = input("Ready to start? (Y/n)")
        if q.lower() == "y":
            break

    await manager.async_start()
    await manager.async_record()


async def aorchestrate(config: ChimeraPyPipelineConfig) -> None:
    """Orchestrate the pipeline."""
    pipeline, created_nodes = config.get_cp_graph_map()
    manager = config.instantiate_manager()

    await manager.aserve()
    await manager.async_zeroconf(enable=True)

    local_workers = await _connect_workers(manager, config)
    mappings = _get_mappings(config, created_nodes)

    # Commit the graph
    await manager.async_commit(graph=pipeline, mapping=mappings)

    if config.mode == "preview":
        await _pipeline_preview(manager)
    else:
        await _pipeline_record(manager)

    if config.runtime is None:
        while True:
            q = input("Stop? (Y/n)")
            if q.lower() == "y":
                break
    else:
        for _ in tqdm.tqdm(range(config.runtime), desc="Running..."):
            await asyncio.sleep(1)

    await manager.async_stop()
    await manager.async_collect()
    cpe_config.set(
        "manager.timeout.worker-shutdown", config.timeouts.shutdown_timeout
    )

    await manager.async_reset(keep_workers=config.keep_remote_workers)
    await manager.async_shutdown()
    print("Shutting down local workers...")
    for worker in local_workers:
        await worker.async_shutdown()


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
        asyncio.run(aorchestrate(cp_config))

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
