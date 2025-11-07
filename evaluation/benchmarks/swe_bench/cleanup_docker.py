#!/usr/bin/env python3
"""
Emergency Docker cleanup script for freeing disk space.

This script aggressively removes Docker images and build cache to free up disk space.
Use this when disk space is running low during pre-build operations.

Usage:
    python cleanup_docker.py [--keep-base-images] [--dry-run]
"""

import argparse

import docker

from openhands.core.logger import openhands_logger as logger


def get_docker_disk_usage(client):
    """Get Docker disk usage statistics."""
    try:
        df_info = client.df()

        images_size = sum(img.get('Size', 0) for img in df_info.get('Images', []))
        containers_size = sum(c.get('SizeRw', 0) for c in df_info.get('Containers', []))
        volumes_size = sum(
            v.get('UsageData', {}).get('Size', 0) for v in df_info.get('Volumes', [])
        )
        build_cache_size = sum(
            bc.get('Size', 0) for bc in df_info.get('BuildCache', [])
        )

        return {
            'images': images_size,
            'containers': containers_size,
            'volumes': volumes_size,
            'build_cache': build_cache_size,
            'total': images_size + containers_size + volumes_size + build_cache_size,
        }
    except Exception as e:
        logger.warning(f'Could not get disk usage: {e}')
        return None


def format_size(bytes_size):
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f'{bytes_size:.2f} {unit}'
        bytes_size /= 1024.0
    return f'{bytes_size:.2f} PB'


def cleanup_docker(keep_base_images: bool = False, dry_run: bool = False):
    """
    Perform aggressive Docker cleanup.

    Args:
        keep_base_images: If True, keep SWE-bench base images (swebench/*)
        dry_run: If True, only show what would be cleaned without actually cleaning
    """
    client = docker.from_env()

    # Print current disk usage
    logger.info('=' * 80)
    logger.info('DOCKER DISK USAGE (BEFORE CLEANUP)')
    logger.info('=' * 80)

    usage = get_docker_disk_usage(client)
    if usage:
        logger.info(f'Images:       {format_size(usage["images"])}')
        logger.info(f'Containers:   {format_size(usage["containers"])}')
        logger.info(f'Volumes:      {format_size(usage["volumes"])}')
        logger.info(f'Build Cache:  {format_size(usage["build_cache"])}')
        logger.info(f'Total:        {format_size(usage["total"])}')

    if dry_run:
        logger.info('\n🔍 DRY RUN MODE - No actual cleanup will be performed\n')

    # Step 1: Remove stopped containers
    logger.info('\n' + '=' * 80)
    logger.info('Step 1: Removing stopped containers...')
    logger.info('=' * 80)

    if not dry_run:
        result = client.containers.prune()
        count = len(result.get('ContainersDeleted') or [])
        space = result.get('SpaceReclaimed', 0)
        logger.info(f'✅ Removed {count} containers, reclaimed {format_size(space)}')
    else:
        containers = client.containers.list(all=True, filters={'status': 'exited'})
        logger.info(f'Would remove {len(containers)} stopped containers')

    # Step 2: Remove dangling images
    logger.info('\n' + '=' * 80)
    logger.info('Step 2: Removing dangling images (untagged)...')
    logger.info('=' * 80)

    if not dry_run:
        result = client.images.prune(filters={'dangling': True})
        count = len(result.get('ImagesDeleted') or [])
        space = result.get('SpaceReclaimed', 0)
        logger.info(
            f'✅ Removed {count} dangling images, reclaimed {format_size(space)}'
        )
    else:
        dangling = client.images.list(filters={'dangling': True})
        logger.info(f'Would remove {len(dangling)} dangling images')

    # Step 3: Remove OpenHands runtime images
    logger.info('\n' + '=' * 80)
    logger.info('Step 3: Removing OpenHands runtime images...')
    logger.info('=' * 80)

    removed_count = 0
    removed_size = 0

    for image in client.images.list():
        try:
            # Check if this is an OpenHands runtime image
            tags = image.tags if image.tags else []
            is_openhands = any(
                'openhands' in tag.lower() or 'runtime' in tag.lower() for tag in tags
            )

            if is_openhands:
                size = image.attrs.get('Size', 0)
                logger.info(
                    f'  Found: {tags[0] if tags else image.short_id} ({format_size(size)})'
                )

                if not dry_run:
                    try:
                        client.images.remove(image.id, force=True)
                        removed_count += 1
                        removed_size += size
                        logger.info('    ✅ Removed')
                    except Exception as e:
                        logger.warning(f'    ⚠️  Could not remove: {e}')
                else:
                    removed_count += 1
                    removed_size += size

        except Exception as e:
            logger.warning(f'  Error processing image: {e}')

    logger.info(
        f'\n{"Would remove" if dry_run else "Removed"} {removed_count} OpenHands images, {format_size(removed_size)}'
    )

    # Step 4: Remove SWE-bench base images (optional)
    if not keep_base_images:
        logger.info('\n' + '=' * 80)
        logger.info('Step 4: Removing SWE-bench base images...')
        logger.info('=' * 80)

        removed_count = 0
        removed_size = 0

        for image in client.images.list():
            try:
                tags = image.tags if image.tags else []
                is_swebench = any(
                    'swebench' in tag.lower() or 'sweb.eval' in tag.lower()
                    for tag in tags
                )

                if is_swebench:
                    size = image.attrs.get('Size', 0)
                    logger.info(
                        f'  Found: {tags[0] if tags else image.short_id} ({format_size(size)})'
                    )

                    if not dry_run:
                        try:
                            client.images.remove(image.id, force=True)
                            removed_count += 1
                            removed_size += size
                            logger.info('    ✅ Removed')
                        except Exception as e:
                            logger.warning(f'    ⚠️  Could not remove: {e}')
                    else:
                        removed_count += 1
                        removed_size += size

            except Exception as e:
                logger.warning(f'  Error processing image: {e}')

        logger.info(
            f'\n{"Would remove" if dry_run else "Removed"} {removed_count} SWE-bench images, {format_size(removed_size)}'
        )
    else:
        logger.info(
            '\n⏭️  Step 4: Skipping SWE-bench base images (--keep-base-images enabled)'
        )

    # Step 5: Prune build cache
    logger.info('\n' + '=' * 80)
    logger.info('Step 5: Pruning build cache...')
    logger.info('=' * 80)

    if not dry_run:
        result = client.api.prune_builds()
        space = result.get('SpaceReclaimed', 0)
        logger.info(f'✅ Reclaimed {format_size(space)} from build cache')
    else:
        # Can't easily get build cache info without pruning
        logger.info('Would prune all build cache')

    # Step 6: Prune unused volumes
    logger.info('\n' + '=' * 80)
    logger.info('Step 6: Pruning unused volumes...')
    logger.info('=' * 80)

    if not dry_run:
        result = client.volumes.prune()
        count = len(result.get('VolumesDeleted') or [])
        space = result.get('SpaceReclaimed', 0)
        logger.info(f'✅ Removed {count} volumes, reclaimed {format_size(space)}')
    else:
        volumes = client.volumes.list(filters={'dangling': True})
        logger.info(f'Would remove {len(volumes)} dangling volumes')

    # Print final disk usage
    logger.info('\n' + '=' * 80)
    logger.info('DOCKER DISK USAGE (AFTER CLEANUP)')
    logger.info('=' * 80)

    if not dry_run:
        usage = get_docker_disk_usage(client)
        if usage:
            logger.info(f'Images:       {format_size(usage["images"])}')
            logger.info(f'Containers:   {format_size(usage["containers"])}')
            logger.info(f'Volumes:      {format_size(usage["volumes"])}')
            logger.info(f'Build Cache:  {format_size(usage["build_cache"])}')
            logger.info(f'Total:        {format_size(usage["total"])}')
    else:
        logger.info('(Disk usage unchanged - dry run mode)')

    logger.info('\n✅ Cleanup complete!')


def main():
    parser = argparse.ArgumentParser(
        description='Emergency Docker cleanup script to free disk space'
    )
    parser.add_argument(
        '--keep-base-images',
        action='store_true',
        help='Keep SWE-bench base images (only remove OpenHands runtime wrappers)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be cleaned without actually cleaning',
    )

    args = parser.parse_args()

    cleanup_docker(keep_base_images=args.keep_base_images, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
