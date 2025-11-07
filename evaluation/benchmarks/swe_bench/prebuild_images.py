"""
Pre-build OpenHands runtime images for SWE-bench instances.

This script builds the OpenHands runtime wrapper images on top of SWE-bench base images
and pushes them to DockerHub. This allows subsequent evaluations to pull pre-built images
instead of rebuilding them for each instance, significantly speeding up the evaluation process.

Usage:
    python evaluation/benchmarks/swe_bench/prebuild_images.py \
        --dataset princeton-nlp/SWE-bench_Verified \
        --split test \
        --docker-registry ghcr.io/openhands/runtime \
        --num-workers 4
"""

import argparse
import base64
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import docker
import requests
from datasets import load_dataset
from tqdm import tqdm

from evaluation.benchmarks.swe_bench.run_infer import (
    DATASET_TYPE,
    get_instance_docker_image,
    set_dataset_type,
)
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.builder import DockerRuntimeBuilder
from openhands.runtime.utils.runtime_build import (
    build_runtime_image,
    get_hash_for_lock_files,
    get_hash_for_source_files,
    get_runtime_image_repo,
    get_runtime_image_repo_and_tag,
)
from openhands.version import get_version

logger.setLevel(logging.DEBUG)


def cleanup_docker_resources(docker_client, aggressive: bool = False):
    """
    Clean up Docker resources to free disk space.

    Args:
        docker_client: Docker client instance
        aggressive: If True, also prune build cache and unused images
    """
    try:
        logger.info('Running Docker cleanup to free disk space...')

        # Remove dangling images (untagged images)
        dangling = docker_client.images.prune(filters={'dangling': True})
        if dangling.get('ImagesDeleted'):
            logger.info(f'Removed {len(dangling["ImagesDeleted"])} dangling images')

        # Remove stopped containers
        containers = docker_client.containers.prune()
        if containers.get('ContainersDeleted'):
            logger.info(
                f'Removed {len(containers["ContainersDeleted"])} stopped containers'
            )

        if aggressive:
            # Prune build cache
            logger.info('Pruning build cache (this may take a moment)...')
            cache = docker_client.api.prune_builds()
            space_reclaimed = cache.get('SpaceReclaimed', 0)
            logger.info(
                f'Reclaimed {space_reclaimed / (1024**3):.2f} GB from build cache'
            )

            # Prune unused images (not just dangling)
            logger.info('Pruning unused images...')
            unused = docker_client.images.prune(filters={'dangling': False})
            if unused.get('ImagesDeleted'):
                logger.info(f'Removed {len(unused["ImagesDeleted"])} unused images')

    except Exception as e:
        logger.warning(f'Docker cleanup encountered an error (non-fatal): {e}')


def remote_image_exists(
    registry_repo: str, tag: str, docker_client: docker.DockerClient, timeout: int = 6
) -> bool | None:
    """
    Check whether an image manifest exists in a remote registry without pulling the image.

    Returns:
        True if the manifest is present, False if it's absent, None if the check could not be
        conclusively performed (caller may fall back to pulling).
    """
    try:
        # Split registry and repository
        if '/' in registry_repo and (
            '.' in registry_repo.split('/')[0] or ':' in registry_repo.split('/')[0]
        ):
            registry = registry_repo.split('/', 1)[0]
            repo = registry_repo.split('/', 1)[1]
        else:
            # Implicit docker hub
            registry = 'registry-1.docker.io'
            repo = registry_repo

        # Normalize docker.io host
        if registry in ('docker.io', 'index.docker.io'):
            registry = 'registry-1.docker.io'

        manifest_url = f'https://{registry}/v2/{repo}/manifests/{tag}'
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}

        # Try anonymous HEAD first (fast)
        try:
            resp = requests.head(manifest_url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return True
            if resp.status_code == 404:
                return False
            if resp.status_code == 401:
                # Registry requires authentication — continue to auth-based attempts
                logger.debug(
                    f'Anonymous HEAD returned 401 for {manifest_url}; will try authenticated checks'
                )
                # Do not raise here; fall through to auth-based probing below
                pass
            # If we received another non-decisive status (e.g., 405 Method Not Allowed), log it for diagnostics
            if resp.status_code not in (200, 404, 401):
                logger.debug(
                    f'HEAD {manifest_url} returned status {resp.status_code}; headers: {resp.headers}'
                )
        except requests.exceptions.RequestException as req_exc:
            # Network or timeout occurred — fallthrough to auth-based attempts / token flow
            logger.debug(f'Anonymous HEAD request failed for {manifest_url}: {req_exc}')
            pass

        # Try using Docker credentials if available
        try:
            auth_configs = {}
            if hasattr(docker_client.api, '_auth_configs') and hasattr(
                docker_client.api._auth_configs, 'get_all_configs'
            ):
                # docker-py internals: try to read stored auths
                auth_configs = docker_client.api._auth_configs.get_all_configs() or {}
            elif hasattr(docker_client.api, '_auth_configs'):
                auth_configs = docker_client.api._auth_configs or {}

            # Try to find a matching auth entry for the registry
            for key, cfg in auth_configs.items():
                try:
                    if registry in key or key in registry:
                        auth = cfg.get('auth') or cfg.get('IdentityToken')
                        if not auth:
                            continue
                        # If auth is identity token, try Bearer directly
                        if cfg.get('IdentityToken'):
                            token = cfg.get('IdentityToken')
                            headers['Authorization'] = f'Bearer {token}'
                            resp = requests.head(
                                manifest_url, headers=headers, timeout=timeout
                            )
                            if resp.status_code == 200:
                                return True
                            if resp.status_code == 404:
                                return False
                            continue

                        # Otherwise auth is base64(username:password)
                        decoded = base64.b64decode(auth).decode('utf-8')
                        if ':' in decoded:
                            user, pwd = decoded.split(':', 1)
                        else:
                            user, pwd = decoded, ''
                        # Attempt authenticated HEAD
                        resp = requests.head(
                            manifest_url,
                            headers=headers,
                            auth=(user, pwd),
                            timeout=timeout,
                        )
                        if resp.status_code == 200:
                            return True
                        if resp.status_code == 404:
                            return False
                except Exception:
                    # Try next credential
                    continue
        except Exception:
            # If authentication probing fails, return None to let caller fallback
            return None

        # For Docker Hub token flow (best-effort): request an anonymous token then retry
        try:
            if 'registry-1.docker.io' in registry:
                token_url = 'https://auth.docker.io/token'
                params = {
                    'service': 'registry.docker.io',
                    'scope': f'repository:{repo}:pull',
                }
                tresp = requests.get(token_url, params=params, timeout=timeout)
                if tresp.status_code == 200:
                    token = tresp.json().get('token')
                    if token:
                        headers['Authorization'] = f'Bearer {token}'
                        resp = requests.head(
                            manifest_url, headers=headers, timeout=timeout
                        )
                        if resp.status_code == 200:
                            return True
                        if resp.status_code == 404:
                            return False
        except Exception:
            pass

        # Could not conclusively determine - signal caller to fallback
        return None
    except Exception:
        return None


def prebuild_instance_image(
    instance_id: str,
    base_image: str,
    runtime_builder: DockerRuntimeBuilder,
    platform: str = 'linux/amd64',
    push_to_registry: bool = True,
    force_rebuild: bool = False,
    enable_browser: bool = False,
    cleanup_after_push: bool = True,
    max_push_retries: int = 3,
) -> tuple[str, bool, str]:
    """
    Pre-build the OpenHands runtime image for a single SWE-bench instance.

    This function first checks if the image already exists in the remote registry
    (unless force_rebuild=True). If it exists, the build is skipped.

    Args:
        instance_id: The SWE-bench instance ID
        base_image: The SWE-bench base container image
        runtime_builder: Docker runtime builder instance
        platform: Target platform (default: linux/amd64)
        push_to_registry: Whether to push the built image to registry
        force_rebuild: Whether to force rebuild even if image exists in remote registry
        enable_browser: Whether to enable browser support (default: False for SWE-bench)
        cleanup_after_push: Whether to remove local image after successful push (default: True)
        max_push_retries: Maximum number of push retry attempts for transient failures (default: 3)

    Returns:
        Tuple of (instance_id, success, image_name or error_message)
    """
    try:
        # Calculate the expected runtime image name first
        from openhands.runtime.utils.runtime_build import (
            get_runtime_image_repo_and_tag,
        )

        runtime_image_repo, _ = get_runtime_image_repo_and_tag(base_image)
        lock_tag = (
            f'oh_v{get_version()}_{get_hash_for_lock_files(base_image, enable_browser)}'
        )
        source_tag = f'{lock_tag}_{get_hash_for_source_files()}'
        expected_runtime_image = f'{runtime_image_repo}:{source_tag}'

        # Check if image already exists in remote registry (unless force_rebuild)
        if not force_rebuild and push_to_registry:
            logger.info(
                f'[{instance_id}] Fast-checking remote registry for: {expected_runtime_image}'
            )
            try:
                remote_check = remote_image_exists(
                    runtime_image_repo, source_tag, runtime_builder.docker_client
                )
            except Exception:
                remote_check = None

            if remote_check is True:
                logger.info(
                    f'[{instance_id}] ✅ Image already exists in remote registry, skipping build: {expected_runtime_image}'
                )
                return (instance_id, True, expected_runtime_image)

            # If remote check could not conclusively determine existence, fall back to previous method
            if remote_check is None:
                logger.debug(
                    f'[{instance_id}] Remote fast-check inconclusive, falling back to pull-based existence check'
                )
                if runtime_builder.image_exists(
                    expected_runtime_image, pull_from_repo=True
                ):
                    logger.info(
                        f'[{instance_id}] ✅ Image already exists in remote registry (verified by pull), skipping build: {expected_runtime_image}'
                    )
                    return (instance_id, True, expected_runtime_image)

        logger.info(f'[{instance_id}] Building runtime image from base: {base_image}')

        # Build the runtime image (this includes intelligent caching)
        # CRITICAL: enable_browser must match what will be used in run_infer.py
        # Default is False (RUN_WITH_BROWSING defaults to 'false' in run_infer.py)
        runtime_image = build_runtime_image(
            base_image=base_image,
            runtime_builder=runtime_builder,
            platform=platform,
            force_rebuild=force_rebuild,
            enable_browser=enable_browser,
        )

        logger.info(f'[{instance_id}] Built image: {runtime_image}')

        # Push to registry if requested
        if push_to_registry:
            logger.info(f'[{instance_id}] Pushing image to registry: {runtime_image}')
            # Extract repo and tag
            if ':' in runtime_image:
                repo, tag = runtime_image.rsplit(':', 1)
            else:
                repo = runtime_image
                tag = 'latest'

            # Push the image with retry logic
            retry_delay = 10  # Initial delay in seconds
            push_succeeded = False

            for attempt in range(1, max_push_retries + 1):
                try:
                    client = runtime_builder.docker_client
                    client.images.get(runtime_image)

                    # Push with progress - increase timeout for large images
                    # Default timeout is often too short for 500MB-1GB images
                    push_kwargs = {
                        'repository': repo,
                        'tag': tag,
                        'stream': True,
                        'decode': True,
                    }

                    if attempt > 1:
                        logger.info(
                            f'[{instance_id}] Retry attempt {attempt}/{max_push_retries} for push...'
                        )
                    else:
                        logger.info(
                            f'[{instance_id}] Starting push (this may take several minutes for large images)...'
                        )

                    for line in client.api.push(**push_kwargs):
                        if 'error' in line:
                            raise Exception(line['error'])
                        if 'status' in line:
                            status = line['status']
                            progress = line.get('progress', '')
                            # Log detailed progress for monitoring
                            if 'Pushing' in status or 'Pushed' in status:
                                logger.debug(f'[{instance_id}] {status} {progress}')
                            elif status not in [
                                'Preparing',
                                'Waiting',
                                'Layer already exists',
                            ]:
                                logger.info(f'[{instance_id}] {status}')

                    logger.info(
                        f'[{instance_id}] Successfully pushed image: {runtime_image}'
                    )
                    push_succeeded = True

                    # Push succeeded, break out of retry loop
                    break

                except Exception as push_error:
                    error_str = str(push_error)

                    # Check if this is a transient error worth retrying
                    is_transient = any(
                        keyword in error_str.lower()
                        for keyword in [
                            'timeout',
                            'timed out',
                            'connection',
                            'network',
                            'temporary',
                            'unavailable',
                            'reset',
                            'broken pipe',
                        ]
                    )

                    if attempt < max_push_retries and is_transient:
                        # Exponential backoff: 10s, 20s, 40s
                        wait_time = retry_delay * (2 ** (attempt - 1))
                        logger.warning(
                            f'[{instance_id}] Push failed (attempt {attempt}/{max_push_retries}): {error_str}'
                        )
                        logger.info(
                            f'[{instance_id}] Waiting {wait_time}s before retry...'
                        )
                        time.sleep(wait_time)
                    else:
                        # Either max retries reached or non-transient error
                        if attempt >= max_push_retries:
                            logger.error(
                                f'[{instance_id}] Push failed after {max_push_retries} attempts: {error_str}'
                            )
                        else:
                            logger.error(
                                f'[{instance_id}] Push failed with non-retryable error: {error_str}'
                            )
                        return (instance_id, False, f'Push failed: {error_str}')

            # Cleanup on push failure to prevent disk space accumulation
            if not push_succeeded:
                if cleanup_after_push:
                    try:
                        logger.info(
                            f'[{instance_id}] Cleaning up failed image to free disk space: {runtime_image}'
                        )
                        client = runtime_builder.docker_client
                        client.images.remove(runtime_image, force=True)
                        logger.debug(
                            f'[{instance_id}] Successfully removed failed image'
                        )
                    except Exception as cleanup_error:
                        logger.warning(
                            f'[{instance_id}] Failed to cleanup failed image (non-fatal): {str(cleanup_error)}'
                        )
                return (instance_id, False, 'Push failed after all retries')

            # Clean up local image after successful push to save disk space
            if cleanup_after_push:
                try:
                    logger.info(
                        f'[{instance_id}] Cleaning up local image to save disk space: {runtime_image}'
                    )
                    # Remove all tags associated with this image
                    client.images.remove(runtime_image, force=False)
                    logger.debug(f'[{instance_id}] Successfully removed local image')
                except Exception as cleanup_error:
                    # Don't fail the entire operation if cleanup fails
                    logger.warning(
                        f'[{instance_id}] Failed to cleanup local image (non-fatal): {str(cleanup_error)}'
                    )

                # Also cleanup the base SWE-bench image to save more space
                try:
                    logger.info(
                        f'[{instance_id}] Cleaning up base image to save disk space: {base_image}'
                    )
                    client.images.remove(base_image, force=False)
                    logger.debug(f'[{instance_id}] Successfully removed base image')
                except Exception as cleanup_error:
                    # Base image might be in use by other builds, don't worry
                    logger.debug(
                        f'[{instance_id}] Could not remove base image (may be in use): {str(cleanup_error)}'
                    )

        return (instance_id, True, runtime_image)

    except Exception as e:
        error_msg = f'Failed to build image: {str(e)}'
        logger.error(f'[{instance_id}] {error_msg}')
        return (instance_id, False, error_msg)


def prebuild_all_images(
    dataset_name: str,
    split: str,
    num_workers: int = 1,
    eval_limit: int | None = None,
    push_to_registry: bool = True,
    force_rebuild: bool = False,
    platform: str = 'linux/amd64',
    skip_existing: bool = True,
    enable_browser: bool = False,
    cleanup_after_push: bool = True,
    max_push_retries: int = 3,
) -> dict[str, any]:
    """
    Pre-build OpenHands runtime images for all instances in the dataset.

    Uses a two-layer approach to skip existing images:
    1. Pre-scan: Check remote registry before submitting tasks (if skip_existing=True)
    2. Just-in-time: Each worker checks again right before building (respects force_rebuild)

    This ensures we don't waste time on images that were pushed between the pre-scan
    and actual build time (e.g., by another parallel run or manual push).

    Args:
        dataset_name: HuggingFace dataset name (e.g., 'princeton-nlp/SWE-bench_Verified')
        split: Dataset split to use (e.g., 'test')
        num_workers: Number of parallel workers for building images
        eval_limit: Limit number of instances to process (for testing)
        push_to_registry: Whether to push built images to registry
        force_rebuild: Whether to force rebuild even if image exists in remote registry
        platform: Target platform (default: linux/amd64)
        skip_existing: Whether to skip instances whose images already exist (pre-scan check)
        enable_browser: Whether to enable browser support (default: False for SWE-bench)
        cleanup_after_push: Whether to remove local images after push (default: True to save disk space)
        max_push_retries: Maximum number of push retry attempts for transient failures (default: 3)

    Returns:
        Dictionary with statistics about the build process
    """
    # Load dataset
    logger.info(f'Loading dataset {dataset_name} split {split}...')
    dataset = load_dataset(dataset_name, split=split)
    set_dataset_type(dataset_name)

    df = dataset.to_pandas()

    if eval_limit:
        df = df.head(eval_limit)
        logger.info(f'Limited to {eval_limit} instances for testing')

    logger.info(f'Processing {len(df)} instances from {dataset_name}')

    # Initialize Docker client with increased timeout for large image pushes
    # Default timeout (60s) is often too short for 500MB-1GB images
    # Set to 10 minutes to handle slow network connections
    docker_client = docker.from_env(timeout=600)
    runtime_builder = DockerRuntimeBuilder(docker_client)

    # Prepare instance list
    instances_to_build = []
    skipped_instances = []

    for _, instance in df.iterrows():
        instance_id = instance['instance_id']

        # Determine if we're using official SWE-Bench images
        use_swebench_official_image = DATASET_TYPE != 'SWE-Gym'

        base_image = get_instance_docker_image(
            instance_id, swebench_official_image=use_swebench_official_image
        )

        # Check if runtime image already exists (if skip_existing is True)
        if skip_existing:
            # CRITICAL: Must match the exact tag naming strategy used in build_runtime_image_in_folder
            # The enable_browser parameter affects the lock_tag hash, so it must match
            runtime_image_repo, _ = get_runtime_image_repo_and_tag(base_image)
            lock_tag = f'oh_v{get_version()}_{get_hash_for_lock_files(base_image, enable_browser)}'
            source_tag = f'{lock_tag}_{get_hash_for_source_files()}'
            expected_image = f'{runtime_image_repo}:{source_tag}'

            # pull_from_repo=True means it will try to pull from remote registry if not found locally
            if runtime_builder.image_exists(expected_image, pull_from_repo=True):
                logger.info(
                    f'[{instance_id}] Image already exists: {expected_image}, skipping'
                )
                skipped_instances.append(instance_id)
                continue

        instances_to_build.append(
            {'instance_id': instance_id, 'base_image': base_image}
        )
        print(f'[{instance_id}] Scheduled for build with base image: {base_image}')
    logger.info(
        f'Building {len(instances_to_build)} images, skipped {len(skipped_instances)} existing images'
    )

    # Warn about disk space if not cleaning up
    if not cleanup_after_push and push_to_registry:
        logger.warning(
            '\n⚠️  cleanup_after_push=False: Local images will NOT be removed after push.\n'
            f'   Building {len(instances_to_build)} images may require significant disk space.\n'
            '   Consider enabling cleanup to save disk space.\n'
        )
    elif cleanup_after_push and push_to_registry:
        logger.info(
            'cleanup_after_push=True: Local images will be removed after successful push to save disk space'
        )

    # Build images in parallel
    results = {
        'total': len(df),
        'to_build': len(instances_to_build),
        'skipped': len(skipped_instances),
        'success': [],
        'failed': [],
    }

    if len(instances_to_build) == 0:
        logger.info('No images to build!')
        return results

    # Run initial cleanup before starting builds
    logger.info('Running initial Docker cleanup before building...')
    cleanup_docker_resources(docker_client, aggressive=True)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all build tasks
        future_to_instance = {
            executor.submit(
                prebuild_instance_image,
                inst['instance_id'],
                inst['base_image'],
                runtime_builder,
                platform,
                push_to_registry,
                force_rebuild,
                enable_browser,  # Pass enable_browser to ensure consistent hashing
                cleanup_after_push,  # Pass cleanup flag
                max_push_retries,  # Pass retry count for push failures
            ): inst['instance_id']
            for inst in instances_to_build
        }

        # Process completed tasks with progress bar
        completed_count = 0
        with tqdm(total=len(instances_to_build), desc='Building images') as pbar:
            for future in as_completed(future_to_instance):
                instance_id, success, result = future.result()

                if success:
                    results['success'].append(
                        {'instance_id': instance_id, 'image': result}
                    )
                    logger.info(f'✅ [{instance_id}] Success: {result}')
                else:
                    results['failed'].append(
                        {'instance_id': instance_id, 'error': result}
                    )
                    logger.error(f'❌ [{instance_id}] Failed: {result}')

                pbar.update(1)
                completed_count += 1

                # Run periodic cleanup every 10 images to prevent disk space issues
                # IMPORTANT: Use aggressive=True to also prune build cache, which can grow to 100s of GB
                if completed_count % 10 == 0:
                    logger.info(
                        f'Running periodic cleanup after {completed_count} images...'
                    )
                    cleanup_docker_resources(docker_client, aggressive=True)

    # Final cleanup after all builds complete
    logger.info('Running final Docker cleanup...')
    cleanup_docker_resources(docker_client, aggressive=True)

    # Print summary
    logger.info('=' * 80)
    logger.info('BUILD SUMMARY')
    logger.info('=' * 80)
    logger.info(f'Total instances: {results["total"]}')
    logger.info(f'To build: {results["to_build"]}')
    logger.info(f'Skipped (existing): {results["skipped"]}')
    logger.info(f'Successfully built: {len(results["success"])}')
    logger.info(f'Failed: {len(results["failed"])}')

    if results['failed']:
        logger.warning('\nFailed instances:')
        for failed in results['failed']:
            logger.warning(f'  - {failed["instance_id"]}: {failed["error"]}')

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Pre-build OpenHands runtime images for SWE-bench instances'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='princeton-nlp/SWE-bench_Verified',
        help='HuggingFace dataset name (default: princeton-nlp/SWE-bench_Verified)',
    )
    parser.add_argument(
        '--split',
        type=str,
        default='test',
        help='Dataset split to use (default: test)',
    )
    parser.add_argument(
        '--num-workers',
        type=int,
        default=1,
        help='Number of parallel workers for building images (default: 1)',
    )
    parser.add_argument(
        '--eval-limit',
        type=int,
        default=None,
        help='Limit number of instances to process (for testing)',
    )
    parser.add_argument(
        '--docker-registry',
        type=str,
        default=None,
        help='Docker registry to push images to (default: from OH_RUNTIME_RUNTIME_IMAGE_REPO env var or ghcr.io/openhands/runtime)',
    )
    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Do not push images to registry (only build locally)',
    )
    parser.add_argument(
        '--force-rebuild',
        action='store_true',
        help='Force rebuild even if image already exists',
    )
    parser.add_argument(
        '--platform',
        type=str,
        default='linux/amd64',
        help='Target platform for Docker images (default: linux/amd64)',
    )
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Do not skip instances whose images already exist',
    )
    parser.add_argument(
        '--enable-browser',
        action='store_true',
        help='Enable browser support (Playwright) in runtime images. Default: False. IMPORTANT: This must match RUN_WITH_BROWSING setting in run_infer.py',
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Do not remove local images after pushing to registry. WARNING: This may consume significant disk space!',
    )
    parser.add_argument(
        '--max-push-retries',
        type=int,
        default=5,
        help='Maximum number of retry attempts for Docker push failures (default: 5)',
    )

    args = parser.parse_args()

    # Set docker registry if provided
    if args.docker_registry:
        os.environ['OH_RUNTIME_RUNTIME_IMAGE_REPO'] = args.docker_registry
        logger.info(f'Using Docker registry: {args.docker_registry}')
    else:
        logger.info(f'Using Docker registry: {get_runtime_image_repo()}')

    # Warn about enable_browser setting
    if args.enable_browser:
        logger.warning(
            '\n⚠️  Building with --enable-browser. Make sure to set RUN_WITH_BROWSING=true '
            'when running evaluations to use these images.\n'
        )
    else:
        logger.info(
            'Building without browser support (default). This matches the default '
            'RUN_WITH_BROWSING=false setting in run_infer.py.'
        )

    # Warn about cleanup setting
    if args.no_cleanup:
        logger.warning(
            '\n⚠️  --no-cleanup enabled: Local images will NOT be removed after push.\n'
            '   This may consume 150-200GB+ of disk space for full SWE-bench datasets!\n'
        )
    else:
        logger.info(
            'Auto-cleanup enabled: Local images will be removed after successful push to save disk space.'
        )

    # Check Docker login if pushing
    if not args.no_push:
        try:
            client = docker.from_env()
            # Try to get auth info
            auth_config = client.api._auth_configs.get_all_configs()
            registry = get_runtime_image_repo().split('/')[0]
            if registry not in auth_config:
                logger.warning(
                    f'\n⚠️  You may not be logged in to {registry}. '
                    f'Images will be built but may fail to push.\n'
                    f'Please run: docker login {registry}\n'
                )
        except Exception as e:
            logger.warning(f'Could not check Docker auth status: {e}')

    # Run the pre-build process
    results = prebuild_all_images(
        dataset_name=args.dataset,
        split=args.split,
        num_workers=args.num_workers,
        eval_limit=args.eval_limit,
        push_to_registry=not args.no_push,
        force_rebuild=args.force_rebuild,
        platform=args.platform,
        skip_existing=not args.no_skip_existing,
        enable_browser=args.enable_browser,
        cleanup_after_push=not args.no_cleanup,
        max_push_retries=args.max_push_retries,
    )

    # Exit with appropriate code
    if results['failed']:
        logger.error(f'\n❌ Build completed with {len(results["failed"])} failures')
        exit(1)
    else:
        logger.info(f'\n✅ Successfully built all {len(results["success"])} images!')
        exit(0)


if __name__ == '__main__':
    main()
