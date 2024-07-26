# Dynamic constructed Dockerfile

This folder builds runtime image (sandbox), which will use a `Dockerfile` that is dynamically generated depends on the `base_image` AND a [Python source distribution](https://docs.python.org/3.10/distutils/sourcedist.html) that's based on the current commit of `opendevin`.

The following command will generate Dockerfile for `ubuntu:22.04` and the source distribution `.tar` into `containers/runtime`.

```bash
poetry run python3 opendevin/runtime/utils/runtime_build.py \
    --base_image ubuntu:22.04 \
    --build_folder containers/runtime
```
