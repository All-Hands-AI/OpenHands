# Custom Sandbox

This folder provides sample files for building and running a [custom sandbox](https://docs.all-hands.dev/modules/usage/how-to/custom-sandbox-guide) you could prompt agents to build and run docker in your workspace.

## Build docker image

```bash
docker buildx bake
```

## Use custom sandbox image

```toml
[sandbox]
base_container_image="custom-sandbox"
runtime_extra_options={privileged=true}
```

See [config.example.toml](config.example.toml) for reference.

For all supported extra options, please visit [Docker SDK for Python](https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run).

## Verify

Just enter the prompt when OpenHands is ready.

```text
I want to test docker
```
