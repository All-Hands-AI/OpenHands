# Pre-building OpenHands Runtime Images for SWE-bench

## Problem

OpenHands builds a runtime wrapper image on top of each SWE-bench base image. This build process takes **~4-5 minutes per instance**, which becomes a significant bottleneck when evaluating hundreds of instances.

Even though the SWE-bench base images exist in DockerHub, OpenHands still needs to:
1. Pull the SWE-bench base image
2. Build an OpenHands runtime layer on top
3. Install OpenHands dependencies

This happens **every time** you run an evaluation, wasting time and compute resources.

## Solution

This pre-build script solves the problem by:

1. **Building all runtime images once** - Build OpenHands runtime images for all instances in advance
2. **Pushing to DockerHub** - Upload the built images to a Docker registry
3. **Reusing in evaluations** - Subsequent evaluations pull pre-built images instantly

**Time savings**: ~4-5 minutes → ~30 seconds per instance! 🚀

---

## Quick Start

### 1. Login to Docker Registry

First, login to your Docker registry where you'll push the images:

```bash
# For Docker Hub
docker login

# For GitHub Container Registry (ghcr.io)
docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_GITHUB_TOKEN

# For other registries
docker login your-registry.com
```

### 2. Run Pre-build Script

**Option A: Using the shell script (recommended)**

```bash
# Build all images from SWE-bench_Verified with 4 parallel workers
./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified \
    test \
    4

# Test with just 10 instances first
./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified \
    test \
    2 \
    10
```

**Option B: Using Python directly**

```bash
poetry run python evaluation/benchmarks/swe_bench/prebuild_images.py \
    --dataset princeton-nlp/SWE-bench_Verified \
    --split test \
    --num-workers 4
```

### 3. Run Evaluation Normally

After pre-building, run your evaluation as usual:

```bash
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
    llm.eval_qwen3_coder_30b_a3b_instruct \
    HEAD \
    CodeActAgent \
    500 \
    100 \
    8 \
    princeton-nlp/SWE-bench_Verified \
    test
```

The evaluation will automatically pull your pre-built images instead of rebuilding! ✅

## Using Docker Hub (docker.io)

If you're using Docker Hub (docker.io) as your registry, follow these concise steps.

1. Log in to Docker Hub (required to push images):

```bash
docker login
```

2. Configure the registry the prebuild script should use. You can set it in one of two ways:

- Environment variable (recommended):

```bash
export OH_RUNTIME_RUNTIME_IMAGE_REPO="docker.io/<your-username>/openhands-runtime"
```

- CLI flag (one-off run):

```bash
poetry run python evaluation/benchmarks/swe_bench/prebuild_images.py \
    --docker-registry docker.io/<your-username>/openhands-runtime \
    --num-workers 4
```

3. Run the prebuild (example):

```bash
# using the shell wrapper (reads OH_RUNTIME_RUNTIME_IMAGE_REPO if set)
./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified test 4
```

Notes:
- Setting `OH_RUNTIME_RUNTIME_IMAGE_REPO` overrides the repository used by default. The script also accepts `--docker-registry` which takes precedence for that run.
- If you forget to login, pushes will fail with authentication errors; `docker login` is sufficient for normal Docker Hub usage.
- To verify a pushed image, run:

```bash
docker pull docker.io/<your-username>/openhands-runtime:oh_v0.59.0_<lock>_<source>
```

## Configuring registry (short)

- Default lookup: the script uses `OH_RUNTIME_RUNTIME_IMAGE_REPO` environment variable if present; otherwise it falls back to the project default (typically `ghcr.io/openhands/runtime`).
- To switch to Docker Hub permanently for your shell session:

```bash
export OH_RUNTIME_RUNTIME_IMAGE_REPO="docker.io/<your-username>/openhands-runtime"
```

- To run a single prebuild with a different registry (no env change):

```bash
poetry run python evaluation/benchmarks/swe_bench/prebuild_images.py --docker-registry docker.io/<your-username>/openhands-runtime
```

Small troubleshooting tips:
- If the script warns you about auth status, run `docker login` for the registry shown.
- If a fast remote-check appears to fail, enable debug logs (set logger to DEBUG) or try `docker pull` manually to confirm access.

---

## Command Reference

### Shell Script

```bash
./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh <dataset> <split> <num_workers> [eval_limit]
```

**Arguments:**
- `dataset`: HuggingFace dataset name (e.g., `princeton-nlp/SWE-bench_Verified`)
- `split`: Dataset split (e.g., `test`)
- `num_workers`: Number of parallel build workers (recommend 2-8 based on CPU/memory)
- `eval_limit`: (Optional) Limit number of instances for testing

**Environment Variables:**
- `OH_RUNTIME_RUNTIME_IMAGE_REPO`: Docker registry (default: `ghcr.io/openhands/runtime`)
- `NO_PUSH=true`: Build locally without pushing
- `FORCE_REBUILD=true`: Rebuild even if image exists
- `PLATFORM`: Target platform (default: `linux/amd64`)
- `NO_SKIP_EXISTING=true`: Don't skip existing images
- `ENABLE_BROWSER=true`: Enable browser support (must match evaluation setting!)
- `NO_CLEANUP=true`: Keep local images after push (WARNING: uses lots of disk space!)

**Examples:**

```bash
# Use custom registry
export OH_RUNTIME_RUNTIME_IMAGE_REPO="docker.io/myusername/openhands-runtime"
./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified test 4

# Build without pushing (local testing)
NO_PUSH=true ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Lite test 2 5

# Force rebuild all images
FORCE_REBUILD=true ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified test 4

# Keep local images (don't cleanup after push)
NO_CLEANUP=true ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified test 4
```

### Python Script

```bash
poetry run python evaluation/benchmarks/swe_bench/prebuild_images.py [OPTIONS]
```

**Options:**
- `--dataset`: Dataset name (default: `princeton-nlp/SWE-bench_Verified`)
- `--split`: Dataset split (default: `test`)
- `--num-workers`: Parallel workers (default: `1`)
- `--eval-limit`: Limit instances for testing
- `--docker-registry`: Docker registry URL
- `--no-push`: Don't push to registry
- `--force-rebuild`: Force rebuild
- `--platform`: Target platform (default: `linux/amd64`)
- `--no-skip-existing`: Don't skip existing images
- `--enable-browser`: Enable browser support (must match evaluation!)
- `--no-cleanup`: Keep local images after push (WARNING: uses lots of disk!)

**Examples:**

```bash
# Build for SWE-bench_Lite with 4 workers
poetry run python evaluation/benchmarks/swe_bench/prebuild_images.py \
    --dataset princeton-nlp/SWE-bench_Lite \
    --split test \
    --num-workers 4

# Test with 10 instances
poetry run python evaluation/benchmarks/swe_bench/prebuild_images.py \
    --dataset princeton-nlp/SWE-bench_Verified \
    --split test \
    --num-workers 2 \
    --eval-limit 10

# Use custom registry
poetry run python evaluation/benchmarks/swe_bench/prebuild_images.py \
    --dataset princeton-nlp/SWE-bench_Verified \
    --split test \
    --num-workers 4 \
    --docker-registry docker.io/myusername/openhands-runtime

# Keep local images (don't cleanup)
poetry run python evaluation/benchmarks/swe_bench/prebuild_images.py \
    --dataset princeton-nlp/SWE-bench_Verified \
    --split test \
    --num-workers 4 \
    --no-cleanup
```

---

## Disk Space Management

### Automatic Cleanup (Default)

**By default**, the pre-build script **automatically removes local images after successful push** to save disk space.

This is critical because:
- Each runtime image: ~500MB-1GB
- SWE-bench_Verified (217 instances): ~110-150GB
- SWE-bench Full (2,294 instances): ~1-1.5TB

**Without cleanup**, you'd need this much disk space locally! With cleanup, you only need enough space for `num_workers` images at once.

### How It Works

```
Instance 1: Build → Push → Delete Local ✅
Instance 2: Build → Push → Delete Local ✅
Instance 3: Build → Push → Delete Local ✅
...

Disk usage: ~num_workers × 1GB (not num_instances × 1GB!)
```

### Disabling Cleanup

If you want to keep local images (e.g., for local testing):

```bash
# Via shell script
NO_CLEANUP=true ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified test 4

# Via Python script
poetry run python evaluation/benchmarks/swe_bench/prebuild_images.py \
    --dataset princeton-nlp/SWE-bench_Verified \
    --split test \
    --num-workers 4 \
    --no-cleanup
```

⚠️ **WARNING**: This requires **150-200GB+** of free disk space for SWE-bench_Verified!

### Manual Cleanup

If you disabled automatic cleanup or need to clean up manually:

```bash
# Remove all OpenHands runtime images
docker images | grep 'openhands/runtime' | awk '{print $3}' | xargs docker rmi -f

# Full Docker cleanup (removes all unused images)
docker system prune -a -f

# Check disk usage
docker system df
```

---

## How It Works

### Image Layering Strategy

```
┌─────────────────────────────────────────────────────────┐
│  OpenHands Runtime Image (Pre-built & Pushed)           │
│  - OpenHands source code                                │
│  - Python dependencies (poetry)                         │
│  - Micromamba environment                               │
│  - Agent execution server                               │
│  Tag: ghcr.io/openhands/runtime:oh_v0.59.0_hash1_hash2  │
├─────────────────────────────────────────────────────────┤
│  SWE-bench Base Image (Official, from DockerHub)        │
│  - /testbed with repository code                        │
│  - Conda testbed environment                            │
│  - Pre-installed dependencies                           │
│  Tag: docker.io/swebench/sweb.eval.x86_64.django...:... │
└─────────────────────────────────────────────────────────┘
```

### Build Process

For each instance, the script:

1. **Identifies base image**: Gets the SWE-bench base image for the instance
2. **Builds runtime layer**: Adds OpenHands components on top
3. **Intelligent caching**:
   - Checks if exact image already exists (source hash match)
   - Reuses lock image if only source changed (dependency hash match)
   - Rebuilds from scratch only if dependencies changed
4. **Pushes to registry**: Uploads built image for future reuse

### Image Naming Convention

```
ghcr.io/openhands/runtime:oh_v0.59.0_6jy3os2hrph5dtod_2vscsa1r26xqzkcl
                         │          │                  │
                         │          │                  └─ Source code hash (16 chars)
                         │          └──────────────────── Dependency lock hash (16 chars)
                         └─────────────────────────────── OpenHands version
```

This ensures:
- ✅ Same code + dependencies = reuse exact image
- ✅ Code changes only = fast rebuild from lock image
- ✅ Dependency changes = full rebuild (necessary)

---

## Workflow Recommendations

### For Development Teams

**Initial Setup (One-time per dataset):**
```bash
# 1. Pre-build all images for your evaluation dataset
./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified \
    test \
    8

# This takes ~4-5 min × num_instances (parallelized by num_workers)
# For 217 instances with 8 workers: ~2-3 hours total
```

**Daily Evaluations:**
```bash
# 2. Run evaluations - images are pulled instantly!
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
    llm.eval_qwen3_coder_30b_a3b_instruct \
    HEAD \
    CodeActAgent \
    500 \
    100 \
    8 \
    princeton-nlp/SWE-bench_Verified \
    test

# Each instance now starts in ~30 seconds instead of 4-5 minutes!
```

**When You Update OpenHands Code:**
```bash
# 3. If you modify OpenHands source code, rebuild affected images
FORCE_REBUILD=true ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified \
    test \
    8

# Only images with different source hash will actually rebuild
```

### For CI/CD Pipelines

```yaml
# .github/workflows/swebench-eval.yml
jobs:
  prebuild-images:
    runs-on: ubuntu-latest
    steps:
      - name: Login to GitHub Container Registry
        run: echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin

      - name: Pre-build runtime images
        run: |
          ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
            princeton-nlp/SWE-bench_Verified test 4

  run-evaluation:
    needs: prebuild-images
    runs-on: ubuntu-latest
    steps:
      - name: Run SWE-bench evaluation
        run: |
          ./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
            llm.eval_model HEAD CodeActAgent 500 100 8 \
            princeton-nlp/SWE-bench_Verified test
```

---

## Supported Datasets

This script supports all SWE-bench variants:

- ✅ `princeton-nlp/SWE-bench` (Full)
- ✅ `princeton-nlp/SWE-bench_Lite` (300 instances)
- ✅ `princeton-nlp/SWE-bench_Verified` (217 instances)
- ✅ `princeton-nlp/SWE-bench_Multimodal` (Multimodal tasks)
- ✅ `SWE-bench-Live` datasets
- ✅ `SWE-rebench` datasets
- ✅ `SWE-Gym` datasets (uses custom images)

---

## Troubleshooting

### Issue: "Permission denied" when pushing to registry

**Solution:**
```bash
# Ensure you're logged in
docker login ghcr.io -u YOUR_USERNAME

# Or use a personal access token
docker login ghcr.io -u YOUR_USERNAME -p YOUR_TOKEN
```

### Issue: "No space left on device"

**Cause:** Disk full (should be rare with auto-cleanup enabled)

**Solution:**
```bash
# Check if cleanup is enabled (it should be by default)
# If you disabled it with NO_CLEANUP=true, re-enable it

# Clean up Docker manually
docker system prune -a -f

# Remove old runtime images
docker images | grep 'ghcr.io/openhands/runtime' | awk '{print $3}' | xargs docker rmi -f

# Check disk usage
docker system df
df -h
```

**Prevention:** Don't use `NO_CLEANUP=true` unless you have 200GB+ free space

### Issue: Build fails with "pull access denied"

**Solution:**
```bash
# Ensure SWE-bench base images are accessible
docker pull docker.io/swebench/sweb.eval.x86_64.django_1776_django-11333:latest

# If still failing, check your Docker Hub rate limits
```

### Issue: Images exist but evaluation still rebuilds

**Solution:**
```bash
# Ensure registry is correct
echo $OH_RUNTIME_RUNTIME_IMAGE_REPO

# Verify image exists in registry
docker pull ghcr.io/openhands/runtime:oh_v0.59.0_XXX_YYY

# Check that evaluation script uses same registry
grep OH_RUNTIME_RUNTIME_IMAGE_REPO evaluation/benchmarks/swe_bench/scripts/run_infer.sh
```

---

## Performance Comparison

### Before Pre-building

```
Instance 1: [4m 30s] Build + [10m] Evaluation = 14m 30s
Instance 2: [4m 45s] Build + [12m] Evaluation = 16m 45s
Instance 3: [4m 20s] Build + [8m]  Evaluation = 12m 20s
...
Total for 217 instances: ~50-60 hours
```

### After Pre-building

```
Pre-build (one-time): [2-3 hours for all images]

Instance 1: [30s] Pull + [10m] Evaluation = 10m 30s ✨
Instance 2: [25s] Pull + [12m] Evaluation = 12m 25s ✨
Instance 3: [28s] Pull + [8m]  Evaluation = 8m 28s  ✨
...
Total for 217 instances: ~35-40 hours

Savings: 15-20 hours (25-33% faster!) 🚀
```

---

## Advanced Usage

### Building for Multiple Platforms

```bash
# Build for ARM64 (M1/M2 Macs)
PLATFORM=linux/arm64 ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Lite test 2

# Build for both AMD64 and ARM64
for platform in linux/amd64 linux/arm64; do
    PLATFORM=$platform ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
        princeton-nlp/SWE-bench_Lite test 2
done
```

### Using a Private Registry

```bash
# Set custom registry
export OH_RUNTIME_RUNTIME_IMAGE_REPO="myregistry.azurecr.io/openhands/runtime"

# Login
docker login myregistry.azurecr.io

# Pre-build
./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified test 4
```

### Incremental Updates

```bash
# Build only new instances (skip existing)
./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified test 4

# Rebuild everything from scratch
FORCE_REBUILD=true NO_SKIP_EXISTING=true \
./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
    princeton-nlp/SWE-bench_Verified test 4
```

---

## FAQ

**Q: Do I need to pre-build for every evaluation?**
A: No! Pre-build once, then run evaluations multiple times. Only rebuild if you update OpenHands code or dependencies.

**Q: Can I use this with different LLM models?**
A: Yes! The runtime images are LLM-agnostic. Pre-build once, evaluate with any model.

**Q: How much disk space do I need?**
A: With automatic cleanup (default): Only enough for `num_workers` images (~4-8GB). Without cleanup: 150-200GB for SWE-bench_Verified, 1-1.5TB for SWE-bench Full. **Recommendation: Use default cleanup!**

**Q: Can I delete base images after pre-building?**
A: Yes, but keep runtime images! Base images are already on DockerHub and can be re-pulled if needed.

**Q: What if pre-build fails for some instances?**
A: Failed instances will fall back to building during evaluation. Check logs to debug failures, then re-run pre-build for failed instances only.

**Q: Are local images automatically cleaned up?**
A: Yes! By default, images are removed from local Docker after successful push to save disk space. Disable with `NO_CLEANUP=true` if needed (requires lots of disk space).

---

## Contributing

Found an issue or have improvements? Please:
1. Check existing issues/PRs
2. Open an issue describing the problem
3. Submit a PR with fixes

---

## License

This script is part of the OpenHands project and follows the same license.
