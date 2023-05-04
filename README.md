# chimerapy-orchestrator

Proof of concept Reusable Nodes and Orchestration Scheme/ Dashboard Application for ChimeraPy with JSON configuration.

## Installation and Usage (Alpha Only)

### Installation for Orchestrator CLI
Recommended: use a virtual environment with conda.

```bash
$ conda create -n chimerapy-dev python=3.9 -c defaults -c conda-forge
```

Install the system level dependencies for ChimeraPy:
```bash
$ sudo apt-get install ffmpeg libsm6 libxext6 -y
$ sudo apt-get install libportaudio2 libportaudiocpp0 portaudio19-dev libasound-dev libsndfile1-dev portaudio19-dev python3-pyaudio -y
```

The `main` branch of this library is build against the `main` branch of `ChimeraPy`. To install the main branch of `ChimeraPy`, then, install the main branch of this library: run the following commands (in your virtual environment):

```bash
$ conda activate chimerapy-dev
$ git clone https://github.com/oele-isis-vanderbilt/ChimeraPy.git
$ cd ChimeraPy
$ pip install -e ".[test]"
$ cd ..
$ git clone https://github.com/oele-isis-vanderbilt/ChimeraPyOrchestrator.git
$ cd ChimeraPyOrchestrator
$ pip install -e ".[test]"
```


### Usage for Orchestrator CLI
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

### Orchestrator CLI Example
In the [`configs`](./configs) directory, there are few configuration examples for simple `ChimeraPy` pipelines.

The command below will run a pipeline that uses the screen capture and webcamera node and runs it in a local worker:
```shell
$ cp-orchestrator orchestrate --config configs/local_screen_and_web.json
```

The commands below will run a pipeline that uses the webcamera node and runs it in a remote worker:
```shell
$ cp-orchestrator orchestrate --config configs/local_camera_remote_worker.json
```
In a separate terminal, run the remote worker:
```shell
$ cp-orchestrator orchestrate-worker --config configs/local_camera_remote_worker.json --worker-id worker1
```

### Dashboard
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


**Note:** This is a proof of concept and is not intended for production use.
