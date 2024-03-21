# OpenDevin Shared Abstraction and Components

This is a Python package that contains all the shared abstraction (e.g., Agent) and components (e.g., sandbox, web browser, search API, selenium).

## Sandbox component

Run the docker-based sandbox interactive:

```bash
mkdir workspace
python3 opendevin/sandbox/docker.py -d workspace
```

It will map `./workspace` into the docker container with the folder permission correctly adjusted for current user.

Example screenshot:

<img width="868" alt="image" src="https://github.com/OpenDevin/OpenDevin/assets/38853559/8dedcdee-437a-4469-870f-be29ca2b7c32">
