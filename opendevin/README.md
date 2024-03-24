# OpenDevin Shared Abstraction and Components

This is a Python package that contains all the shared abstraction (e.g., Agent) and components (e.g., sandbox, web browser, search API, selenium).

## Sandbox component

Run the docker-based sandbox interactive:

```bash
mkdir workspace
python3 opendevin/sandbox/sandbox.py -d workspace
```

It will map `./workspace` into the docker container with the folder permission correctly adjusted for current user.

Example screenshot:

<img width="868" alt="image" src="https://github.com/OpenDevin/OpenDevin/assets/38853559/8dedcdee-437a-4469-870f-be29ca2b7c32">


## How to run

1. Build the sandbox image local. If you want to use specific image tags, please also fix the variable in code, in code default image tag is `latest`.
```bash 
docker build -f opendevin/sandbox/Dockerfile -t opendevin/sandbox:v0.1 .
```

2. Set the `OPENAI_API_KEY`, please find more details [here](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety). Also, choose the model you want. Default is `gpt-4-0125-preview`
```bash
export OPENAI_API_KEY=xxxxxxx
```

3. Install the requirement package.
```bash
pip install -r requirements.txt                                                                 
```
If you still meet problem like `ModuleNotFoundError: No module named 'agenthub'`, try to add the `opendevin` root path into `PATH` env.

4. Run following cmd to start.
```bash
PYTHONPATH=`pwd` python ./opendevin/main.py -d ./workspace -t "write a bash script that prints hello world"
```
