# mle-bench

## Setup

### Kaggle API token

Install your Kaggle API token at `~/.kaggle/kaggle.json`.

### MLE-bench

`poetry add git+https://org-14957082@github.com:openai/mle-bench`

### Build images

```bash
docker build --platform=linux/amd64 \
--build-arg PYTHON_VERSION=3.12 \
--build-arg INSTALL_HEAVY_DEPENDENCIES=false \
-t mlebench-env -f environment/Dockerfile .
```
