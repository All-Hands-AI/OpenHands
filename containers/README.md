# Docker Containers

Each folder here contains a Dockerfile, and a config.sh describing how to build
the images and where to push them. These images are built and pushed in GitHub Actions
by the `ghcr.yml` workflow.

## Building Manually

```bash
docker build -f containers/app/Dockerfile -t openhands .
docker build -f containers/sandbox/Dockerfile -t sandbox .
```
