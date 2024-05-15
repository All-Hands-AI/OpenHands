# Docker Containers
Each folder here contains a Dockerfile, and a config.sh describing how to build
the image and where to push it. These are images are built and pushed in GitHub Actions
by the `ghcr.yml` workflow.

## Building Manually

```
docker build -f containers/app/Dockerfile -t opendevin .
docker build -f containers/sandbox/Dockerfile -t sandbox .
```
