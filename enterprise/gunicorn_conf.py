"""
Gunicorn configuration for OpenHands enterprise server with multiprocess Prometheus support.
"""
import os


def child_exit(server, worker):
    """
    Called just after a worker has been exited, in the master process.
    Mark the worker's process as dead in the multiprocess metrics collector.
    This is required for prometheus_client multiprocess mode to work correctly.

    See: https://prometheus.github.io/client_python/multiprocess/
    """
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(worker.pid)


def when_ready(server):
    """
    Called just after the server is started.
    Ensure the multiprocess directory exists and is clean.
    """
    multiproc_dir = os.environ.get('PROMETHEUS_MULTIPROC_DIR')
    if multiproc_dir:
        # Directory cleanup is handled by the container startup script
        # but we ensure it exists
        os.makedirs(multiproc_dir, exist_ok=True)
