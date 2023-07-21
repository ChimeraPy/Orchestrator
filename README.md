<p align="center">
  <a href="https://github.com/ChimeraPy"><img src="./docs/images/banner.png" alt="ChimeraPy"></a>
</p>
<p align="center">
    <em>Reusable Nodes and Orchestration Scheme/ Dashboard Application for ChimeraPy with JSON configuration.</em>
</p>
<p align="center">
<a href="https://github.com/ChimeraPy/ChimeraPy/actions?query=workflow%3ATest" target="_blank">
    <img src="https://github.com/ChimeraPy/ChimeraPy/workflows/Test/badge.svg" alt="Test">
</a>
<a href='https://coveralls.io/github/ChimeraPy/ChimeraPyOrchestrator?branch=main'>
    <img src='https://coveralls.io/repos/github/ChimeraPy/ChimeraPyOrchestrator/badge.svg?branch=main' alt='Coverage Status' />
</a>
</p>


ChimeraPy is a Scientific, Distributed Computing Framework for Real-time Multimodal Data Retrieval and Processing. This package provides reusable nodes and orchestration scheme (CLI)/ and web dashboard application(via REST API) for ChimeraPy with JSON configuration.

## Installation
Package is available on `PyPI`, install with `pip`:
```bash
$ pip install chimerapy-orchestrator
```

## Usage for Orchestrator CLI
Installation provides  `cp-orchestrator` command:

```shell
$ cp-orchestrator --help
usage: The CP orchestrator [-h] {orchestrate,orchestrate-worker,list-remote-workers,server} ...

options:
  -h, --help            show this help message and exit

subcommands:
  valid subcommands

  {orchestrate,orchestrate-worker,list-remote-workers,server}
    orchestrate         Orchestrate the pipeline
    orchestrate-worker  Orchestrate a worker
    list-remote-workers
                        List the remote workers
    server              Start the server
```

Specific subcommands also have their own help messages, and can be used `cp-orchestrator <subcommand> --help`.

## Orchestrator CLI Example
In the [`configs`](./configs) directory, there are few configuration examples for simple `ChimeraPy` pipelines.

The command below will run a pipeline that uses the webcamera and showwindow nodes and runs it in a local worker:
```shell
$ cp-orchestrator orchestrate --config configs/local_camera.json
```

The commands below will run a pipeline that uses the webcamera node and runs it in a remote worker:
```shell
$ cp-orchestrator orchestrate --config configs/local_camera_remote_worker.json
```
In a separate terminal, run the remote worker:
```shell
$ cp-orchestrator orchestrate-worker --config configs/local_camera_remote_worker.json --worker-id worker1
```

## Dashboard
The dashboard application is still in early stages of development and can't be used directly yet. However, it can be run in development mode.
To run the dashboard, run the backend server first:

```shell
$ cp-orchestrator server --server-port 8000
```

Then, in a separate terminal, run the dashboard:
```shell
$ cd dashboard
$ npm install
$ npm run dev
```

Finally, open a browser and navigate to `http://localhost:5173` for the dashboard.

## Contributing
Contributions are welcomed! Our [Developer Documentation](https://chimerapy.readthedocs.io/en/latest/developer/index.html) should provide more details in how ChimeraPy works and what is in current development.

## License
[ChimeraPy](https://github.com/ChimeraPy) and [ChimeraPy/Orchestrator](https://github.com/ChimeraPy/Orchestrator) uses the GNU GENERAL PUBLIC LICENSE, as found in [LICENSE](./LICENSE) file.

## Funding Info
This project is supported by the [National Science Foundation](https://www.nsf.gov/) under AI Institute  Grant No. [DRL-2112635](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2112635&HistoricalAwards=false).
