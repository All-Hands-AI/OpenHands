# OpenHands Command Line Interface

A user-friendly wrapper for running OpenHands in docker container.
Multiple instances can be started to work in different workspaces.

The CLI performs the following:

* Check docker installation. If not found, open the Docker installation page in a browser
* Validate user inputs and provide defaults for required arguments
* Pull the docker image and start OpenHands
* Launch the OpenHands Web UI in a browser

## Build and run

Makefile and scripts are provided for building the CLI for the following platforms.

* Linux
* MacOS
* Windows

Other plaforms can be added if required.

### Build in docker

```bash
make build
# same as
./build.sh
```

Alternatively, one can also build on host if [Go toolchain](https://go.dev/doc/install) has been installed.

```bash
./build-cli.sh
```

### Run with make or the script on host

You may set default model and API key with env: LLM_MODEL and LLM_API_KEY.

```bash
export LLM_MODEL="openai/gpt-4o"
export LLM_API_KEY="sk_..."
#
make run ARGS="..."
# same as
./run-cli.sh ARGS...
```

### Add to PATH and run the CLI directly

The binaries are in `./dist/` after the build.

```bash
openhands [flags] WORKSPACE [-- [OPTION...] -- [COMMAND] [ARG...]]
```

`OPTION`, `COMMAND`, and `ARG` can be optionally passed on to the docker command, useful if you are running custom images during development.

The following is an example of running the `openhands:dev` image:

```bash
openhands --image openhands:dev /tmp/ws -- --rm --tty --workdir /app -v $HOME/my/devin/OpenHands/:/app -e BACKEND_HOST=0.0.0.0 -e SANDBOX_API_HOSTNAME=host.docker.internal -- make run
```

## CLI help message

```bash
make run ARGS="--help"
./run-cli.sh --help
openhands --help

```

```bash
OpenHands: Code Less, Make More

Welcome to OpenHands (formerly OpenDevin), a platform for software development agents powered by AI.

OpenHands agents can do anything a human developer can: modify code, run commands,
browse the web, call APIs, and yes—even copy code snippets from StackOverflow.

Learn more at https://docs.all-hands.dev/.

Usage:
  openhands WORKSPACE  [flags]

Flags:
      --browse               Open OpenHands Platform UI in a browser (default true)
  -h, --help                 Display help and exit
      --image string         Specify the OpenHands Docker image (default "ghcr.io/all-hands-ai/openhands:0.9")
      --llm-api-key string   Specify the LLM API key
      --llm-model string     Specify the LLM model
  -p, --port int             Port to use for the OpenHands Platform server. default auto select
      --sandbox string       Specify the Sandbox Docker image (default "ghcr.io/all-hands-ai/runtime:0.9-nikolaik")
      --version              Display version and exit
```

For a complete list of supported docker OPTIONS:

```bash
docker run --help
```
