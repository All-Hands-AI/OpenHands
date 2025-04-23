# Runtime Refactoring Proof of Concept

This document provides a proof-of-concept implementation for the proposed runtime refactoring approach.

## Proof of Concept Implementation

### 1. Dependencies Dockerfile

First, we'll create a Dockerfile that builds all dependencies into the `/openhands` folder:

```dockerfile
# Base Dependencies Dockerfile
FROM ubuntu:22.04 as openhands-deps

# Set environment variables
ENV POETRY_VIRTUALENVS_PATH=/openhands/poetry \
    MAMBA_ROOT_PREFIX=/openhands/micromamba \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    EDITOR=code \
    VISUAL=code \
    GIT_EDITOR="code --wait" \
    OPENVSCODE_SERVER_ROOT=/openhands/.openvscode-server

# Install base system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget curl ca-certificates sudo apt-utils git jq build-essential ripgrep \
        libgl1-mesa-glx libasound2-plugins libatomic1 && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    TZ=Etc/UTC DEBIAN_FRONTEND=noninteractive \
        apt-get install -y --no-install-recommends nodejs python3.12 python-is-python3 python3-pip python3.12-venv && \
    corepack enable yarn && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up Node.js and Python tools
RUN ln -s "$(dirname $(which node))/corepack" /usr/local/bin/corepack && \
    npm install -g corepack && corepack enable yarn && \
    curl -fsSL --compressed https://install.python-poetry.org | python - && \
    curl -LsSf https://astral.sh/uv/install.sh | sh

# Create necessary directories
RUN mkdir -p /openhands && \
    mkdir -p /openhands/logs && \
    mkdir -p /openhands/poetry && \
    mkdir -p /openhands/bin && \
    mkdir -p /openhands/lib

# Install tmux and its dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends tmux libevent-dev libncurses-dev && \
    cp $(which tmux) /openhands/bin/ && \
    # Copy tmux dependencies
    ldd $(which tmux) | grep -v linux-vdso.so.1 | awk '{print $3}' | xargs -I{} cp -L {} /openhands/lib/ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install micromamba
RUN mkdir -p /openhands/micromamba/bin && \
    /bin/bash -c "PREFIX_LOCATION=/openhands/micromamba BIN_FOLDER=/openhands/micromamba/bin INIT_YES=no CONDA_FORGE_YES=yes $(curl -L https://micro.mamba.pm/install.sh)" && \
    /openhands/micromamba/bin/micromamba config remove channels defaults && \
    /openhands/micromamba/bin/micromamba config list

# Create the openhands virtual environment and install poetry and python
RUN /openhands/micromamba/bin/micromamba create -n openhands -y && \
    /openhands/micromamba/bin/micromamba install -n openhands -c conda-forge poetry python=3.12 -y

# Create a clean openhands directory including only the pyproject.toml, poetry.lock and openhands/__init__.py
RUN mkdir -p /openhands/code/openhands && \
    touch /openhands/code/openhands/__init__.py

# Copy project files (in a real implementation, these would be copied from the host)
COPY ./pyproject.toml ./poetry.lock /openhands/code/

# Configure micromamba and poetry
RUN /openhands/micromamba/bin/micromamba config set changeps1 False && \
    /openhands/micromamba/bin/micromamba run -n openhands poetry config virtualenvs.path /openhands/poetry && \
    /openhands/micromamba/bin/micromamba run -n openhands poetry env use python3.12

# Install project dependencies
RUN /openhands/micromamba/bin/micromamba run -n openhands poetry install --only main --no-interaction --no-root && \
    /openhands/micromamba/bin/micromamba run -n openhands poetry install --only runtime --no-interaction --no-root

# Install playwright and its dependencies
RUN apt-get update && \
    /openhands/micromamba/bin/micromamba run -n openhands poetry run pip install playwright && \
    /openhands/micromamba/bin/micromamba run -n openhands poetry run playwright install --with-deps chromium && \
    # Copy Chromium to /openhands/browser
    mkdir -p /openhands/browser && \
    cp -r /root/.cache/ms-playwright /openhands/browser/ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables and permissions
RUN /openhands/micromamba/bin/micromamba run -n openhands poetry run python -c "import sys; print('OH_INTERPRETER_PATH=' + sys.executable)" >> /etc/environment && \
    chmod -R g+rws /openhands/poetry && \
    mkdir -p /openhands/workspace && chmod -R g+rws,o+rw /openhands/workspace

# Setup VSCode Server
ARG RELEASE_TAG="openvscode-server-v1.98.2"
ARG RELEASE_ORG="gitpod-io"

RUN arch=$(uname -m) && \
    if [ "${arch}" = "x86_64" ]; then \
        arch="x64"; \
    elif [ "${arch}" = "aarch64" ]; then \
        arch="arm64"; \
    elif [ "${arch}" = "armv7l" ]; then \
        arch="armhf"; \
    fi && \
    wget https://github.com/${RELEASE_ORG}/openvscode-server/releases/download/${RELEASE_TAG}/${RELEASE_TAG}-linux-${arch}.tar.gz && \
    tar -xzf ${RELEASE_TAG}-linux-${arch}.tar.gz && \
    if [ -d "${OPENVSCODE_SERVER_ROOT}" ]; then rm -rf "${OPENVSCODE_SERVER_ROOT}"; fi && \
    mv ${RELEASE_TAG}-linux-${arch} ${OPENVSCODE_SERVER_ROOT} && \
    cp ${OPENVSCODE_SERVER_ROOT}/bin/remote-cli/openvscode-server ${OPENVSCODE_SERVER_ROOT}/bin/remote-cli/code && \
    rm -f ${RELEASE_TAG}-linux-${arch}.tar.gz

# Create wrapper scripts
RUN echo '#!/bin/bash\nexport LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH\nexec /openhands/bin/tmux "$@"' > /openhands/bin/oh-tmux && \
    chmod +x /openhands/bin/oh-tmux

RUN echo '#!/bin/bash\nexport PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright\nexec /openhands/micromamba/bin/micromamba run -n openhands poetry run playwright "$@"' > /openhands/bin/oh-playwright && \
    chmod +x /openhands/bin/oh-playwright

# Clear caches
RUN /openhands/micromamba/bin/micromamba run -n openhands poetry cache clear --all . -n && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    /openhands/micromamba/bin/micromamba clean --all
```

### 2. Target Image Dockerfile

Next, we'll create a Dockerfile that uses the dependencies image to create the final runtime image:

```dockerfile
# Target Image Dockerfile
FROM openhands-deps:latest as deps

# Use any base image
FROM alpine:latest

# Copy the /openhands folder from the deps image
COPY --from=deps /openhands /openhands

# Set up environment variables
ENV PATH=/openhands/bin:$PATH \
    LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH \
    POETRY_VIRTUALENVS_PATH=/openhands/poetry \
    MAMBA_ROOT_PREFIX=/openhands/micromamba \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    EDITOR=code \
    VISUAL=code \
    GIT_EDITOR="code --wait" \
    OPENVSCODE_SERVER_ROOT=/openhands/.openvscode-server \
    PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright

# Install minimal dependencies required by the base system
RUN apk add --no-cache bash ca-certificates libstdc++ gcompat

# Create openhands user
RUN addgroup -g 1000 openhands && \
    adduser -D -u 1000 -G openhands openhands && \
    mkdir -p /workspace && \
    chown -R openhands:openhands /workspace /openhands

# Set the working directory
WORKDIR /workspace

# Switch to the openhands user
USER openhands

# Command to start the action execution server
CMD ["/openhands/micromamba/bin/micromamba", "run", "-n", "openhands", "poetry", "run", "python", "-m", "openhands.runtime.action_execution_server", "8000", "--working-dir", "/workspace"]
```

### 3. Modified Runtime Builder

Here's a sketch of how the runtime builder could be modified to support this approach:

```python
def build_runtime_image(
    base_image: str,
    runtime_builder: RuntimeBuilder,
    use_deps_image: bool = False,
    deps_image: str = "openhands-deps:latest",
    platform: str | None = None,
    extra_deps: str | None = None,
    build_folder: str | None = None,
    dry_run: bool = False,
    force_rebuild: bool = False,
    extra_build_args: List[str] | None = None,
) -> str:
    """Builds the OpenHands runtime Docker image.
    
    If use_deps_image is True, it will use the dependencies image approach.
    Otherwise, it will use the traditional approach.
    """
    if use_deps_image:
        return build_runtime_image_from_deps(
            base_image=base_image,
            runtime_builder=runtime_builder,
            deps_image=deps_image,
            platform=platform,
            extra_deps=extra_deps,
            build_folder=build_folder,
            dry_run=dry_run,
            extra_build_args=extra_build_args,
        )
    else:
        # Use the existing implementation for the traditional approach
        return build_runtime_image_traditional(
            base_image=base_image,
            runtime_builder=runtime_builder,
            platform=platform,
            extra_deps=extra_deps,
            build_folder=build_folder,
            dry_run=dry_run,
            force_rebuild=force_rebuild,
            extra_build_args=extra_build_args,
        )

def build_runtime_image_from_deps(
    base_image: str,
    runtime_builder: RuntimeBuilder,
    deps_image: str = "openhands-deps:latest",
    platform: str | None = None,
    extra_deps: str | None = None,
    build_folder: str | None = None,
    dry_run: bool = False,
    extra_build_args: List[str] | None = None,
) -> str:
    """Builds a runtime image by copying the /openhands folder from a dependencies image."""
    if build_folder is None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = build_runtime_image_from_deps_in_folder(
                base_image=base_image,
                runtime_builder=runtime_builder,
                deps_image=deps_image,
                build_folder=Path(temp_dir),
                extra_deps=extra_deps,
                dry_run=dry_run,
                platform=platform,
                extra_build_args=extra_build_args,
            )
            return result

    result = build_runtime_image_from_deps_in_folder(
        base_image=base_image,
        runtime_builder=runtime_builder,
        deps_image=deps_image,
        build_folder=Path(build_folder),
        extra_deps=extra_deps,
        dry_run=dry_run,
        platform=platform,
        extra_build_args=extra_build_args,
    )
    return result

def build_runtime_image_from_deps_in_folder(
    base_image: str,
    runtime_builder: RuntimeBuilder,
    deps_image: str,
    build_folder: Path,
    extra_deps: str | None,
    dry_run: bool,
    platform: str | None = None,
    extra_build_args: List[str] | None = None,
) -> str:
    """Prepares the build folder and builds the runtime image using the dependencies image."""
    runtime_image_repo, _ = get_runtime_image_repo_and_tag(base_image)
    lock_tag = f'oh_v{oh_version}_{get_hash_for_lock_files(base_image)}'
    versioned_tag = f'oh_v{oh_version}_{get_tag_for_versioned_image(base_image)}'
    versioned_image_name = f'{runtime_image_repo}:{versioned_tag}'
    source_tag = f'{lock_tag}_{get_hash_for_source_files()}'
    hash_image_name = f'{runtime_image_repo}:{source_tag}'

    logger.info(f'Building image: {hash_image_name}')
    
    # Create a Dockerfile that copies from the deps image
    dockerfile_content = _generate_dockerfile_from_deps(
        base_image=base_image,
        deps_image=deps_image,
        extra_deps=extra_deps,
    )
    
    with open(Path(build_folder, 'Dockerfile'), 'w') as file:
        file.write(dockerfile_content)
    
    if not dry_run:
        _build_sandbox_image(
            build_folder,
            runtime_builder,
            runtime_image_repo,
            source_tag=source_tag,
            lock_tag=lock_tag,
            versioned_tag=versioned_tag,
            platform=platform,
            extra_build_args=extra_build_args,
        )
    
    return hash_image_name

def _generate_dockerfile_from_deps(
    base_image: str,
    deps_image: str,
    extra_deps: str | None = None,
) -> str:
    """Generate a Dockerfile that copies from the deps image."""
    env = Environment(
        loader=FileSystemLoader(
            searchpath=os.path.join(os.path.dirname(__file__), 'runtime_templates')
        )
    )
    template = env.get_template('Dockerfile_from_deps.j2')

    dockerfile_content = template.render(
        base_image=base_image,
        deps_image=deps_image,
        extra_deps=extra_deps if extra_deps is not None else '',
    )
    return dockerfile_content
```

### 4. Dockerfile Template for Dependencies Approach

Create a new template file `Dockerfile_from_deps.j2`:

```jinja
FROM {{ deps_image }} as deps

FROM {{ base_image }}

# Copy the /openhands folder from the deps image
COPY --from=deps /openhands /openhands

# Set up environment variables
ENV PATH=/openhands/bin:$PATH \
    LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH \
    POETRY_VIRTUALENVS_PATH=/openhands/poetry \
    MAMBA_ROOT_PREFIX=/openhands/micromamba \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    EDITOR=code \
    VISUAL=code \
    GIT_EDITOR="code --wait" \
    OPENVSCODE_SERVER_ROOT=/openhands/.openvscode-server \
    PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright

# Install extra dependencies if specified
{% if extra_deps %}RUN {{ extra_deps }} {% endif %}

# Create openhands user if it doesn't exist
RUN if ! id -u openhands > /dev/null 2>&1; then \
        groupadd -g 1000 openhands || true && \
        useradd -u 1000 -g 1000 -m -s /bin/bash openhands || true; \
    fi && \
    mkdir -p /workspace && \
    chown -R openhands:openhands /workspace /openhands

# Set the working directory
WORKDIR /workspace
```

## Testing the Approach

To test this approach, you would:

1. Build the dependencies image:
   ```bash
   docker build -t openhands-deps:latest -f Dockerfile.deps .
   ```

2. Build a runtime image using various base images:
   ```bash
   # Using Alpine
   docker build -t openhands-alpine:latest -f Dockerfile.alpine .
   
   # Using Ubuntu
   docker build -t openhands-ubuntu:latest -f Dockerfile.ubuntu .
   
   # Using Debian
   docker build -t openhands-debian:latest -f Dockerfile.debian .
   ```

3. Test each image to ensure all components work correctly:
   ```bash
   # Test tmux
   docker run --rm openhands-alpine:latest /openhands/bin/oh-tmux -V
   
   # Test Chromium
   docker run --rm openhands-alpine:latest /openhands/bin/oh-playwright --version
   
   # Test the action execution server
   docker run --rm -p 8000:8000 openhands-alpine:latest
   ```

## Conclusion

This proof-of-concept demonstrates how the proposed approach could be implemented. The key advantages are:

1. **Modularity**: Clear separation between dependencies and the base image
2. **Flexibility**: Ability to use any base image
3. **Efficiency**: Faster builds by reusing the pre-built dependencies image

The main challenges are ensuring binary compatibility and proper environment setup, which are addressed through wrapper scripts and environment variables.