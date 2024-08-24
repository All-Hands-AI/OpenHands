# Docker Containers

Each folder here contains a Dockerfile, and a config.sh describing how to build
the images and where to push them. These images are built and pushed in GitHub Actions
by the `ghcr.yml` workflow.

## Building Manually

```bash
docker build -f containers/app/Dockerfile -t openhands .
docker build -f containers/sandbox/Dockerfile -t sandbox .
```

Here's a simplified README explaining the `build.sh` script, focusing on the Docker commands:

## build.sh Script README

This script automates the process of building and optionally pushing Docker images for the OpenHands project.

### What does this script do?

1. Sets up image names, tags, and build configurations.
2. Determines which tags to use based on Git information and user input.
3. Builds a Docker image using `docker buildx build` with various optimizations.

### Key Docker Commands Explained

The main Docker command used is `docker buildx build`. Here's what it does in simple terms:

1. **Building for multiple platforms**:

   ```sh
   --platform linux/amd64,linux/arm64
   ```

   This builds the image for both Intel/AMD and ARM-based computers.

2. **Tagging the image**:

   ```sh
   -t $DOCKER_REPOSITORY:$tag
   ```

   This gives the image one or more names (tags) for easy reference.

3. **Caching for faster builds**:

   ```sh
   --cache-from=type=registry,ref=$DOCKER_REPOSITORY:$cache_tag
   ```

   This uses previously built parts of the image to speed up the build process.

4. **Pushing to a registry** (if requested):

   ```sh
   --push
   ```

   This uploads the built image to a central storage (registry) for others to use.

5. **Specifying the build context**:

   ```sh
   "$DOCKER_BASE_DIR"
   ```

   This tells Docker where to find the files needed for building the image.

### How to use the script

Run the script with these arguments:

```sh
./build.sh <image_name> <org_name> [--push] [tag_suffix]
```

- `<image_name>`: The name of the image to build (e.g., "openhands", "runtime")
- `<org_name>`: Your organization name
- `--push`: (Optional) If included, pushes the image to the registry
- `[tag_suffix]`: (Optional) Adds a suffix to the image tags

The script handles the complexities of building, tagging, and optionally pushing Docker images, making it easier for developers to manage the build process.
