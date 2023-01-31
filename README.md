# chimerapy-orchestrator

Proof of concept Reusable Nodes and Orchestration Scheme for ChimeraPy with JSON configuration.

## Install
In your `ChimeraPy` dev environment, install the package:

```shell
$ git clone git@github.com:oele-isis-vanderbilt/ChimeraPyOrchestrator.git
$ cd chimerapy-orchestrator
$ pip install [-e] .
```

## Usage
A single entrypoint is registered `cp-orchestrator`:

```shell
usage: The CP orchestrator [-h] [--config CONFIG] {orchestrate}

positional arguments:
  {orchestrate}    The mode for the orchestrator

options:
  -h, --help       show this help message and exit
  --config CONFIG  The configuration file to use (default: None)
```

An example config file can be found [here](configs/local_camera.json).

**Notes: This is in a Very initial phase of prototyping. However, can be helpful for thinking about user actions and frontend setup.**
