"""Utilities for getting system resource statistics."""

import time

import psutil


def get_system_stats() -> dict:
    """Get current system resource statistics.

    Returns:
        dict: A dictionary containing:
            - cpu_percent: CPU usage percentage for the current process
            - memory: Memory usage stats (rss, vms, percent)
            - disk: Disk usage stats (total, used, free, percent)
            - io: I/O statistics (read/write bytes)
    """
    process = psutil.Process()
    # Get initial CPU percentage (this will return 0.0)
    process.cpu_percent()
    # Wait a bit and get the actual CPU percentage
    time.sleep(0.1)

    with process.oneshot():
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

    disk_usage = psutil.disk_usage('/')

    # Get I/O stats directly from /proc/[pid]/io to avoid psutil's field name assumptions
    try:
        with open(f'/proc/{process.pid}/io', 'rb') as f:
            io_stats = {}
            for line in f:
                if line:
                    try:
                        name, value = line.strip().split(b': ')
                        io_stats[name.decode('ascii')] = int(value)
                    except (ValueError, UnicodeDecodeError):
                        continue
    except (FileNotFoundError, PermissionError):
        io_stats = {'read_bytes': 0, 'write_bytes': 0}

    return {
        'cpu_percent': cpu_percent,
        'memory': {
            'rss': memory_info.rss,
            'vms': memory_info.vms,
            'percent': memory_percent,
        },
        'disk': {
            'total': disk_usage.total,
            'used': disk_usage.used,
            'free': disk_usage.free,
            'percent': disk_usage.percent,
        },
        'io': {
            'read_bytes': io_stats.get('read_bytes', 0),
            'write_bytes': io_stats.get('write_bytes', 0),
        },
    }
