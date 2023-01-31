import json
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from .pipeline_config import ChimeraPyPipelineConfig


def orchestrate(config: ChimeraPyPipelineConfig):
    manager, pipeline, mappings = config.pipeline_graph()

    while True:
        q = input("All workers connected? (Y/n)")
        if q.lower() == "y":
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


def run(args=None):
    parser = ArgumentParser(
        "The CP orchestrator", formatter_class=ArgumentDefaultsHelpFormatter
    )

    modes = [
        "orchestrate",
    ]

    parser.add_argument(
        "mode", help="The mode for the orchestrator", type=str, choices=sorted(modes)
    )
    parser.add_argument("--config", help="The configuration file to use", type=str)

    args = parser.parse_args(args)

    if args.mode == "orchestrate":
        with open(args.config) as config_file:
            config_dict = json.load(config_file)
            cp_config = ChimeraPyPipelineConfig.parse_obj(config_dict)
            orchestrate(cp_config)
    else:
        parser.print_help()
