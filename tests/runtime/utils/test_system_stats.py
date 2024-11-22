"""Tests for system stats utilities."""

import psutil

from openhands.runtime.utils.system_stats import get_system_stats


def test_get_system_stats():
    """Test that get_system_stats returns valid system statistics."""
    stats = get_system_stats()

    # Test structure
    assert isinstance(stats, dict)
    assert set(stats.keys()) == {'cpu_percent', 'memory', 'disk', 'io'}

    # Test CPU stats
    assert isinstance(stats['cpu_percent'], float)
    assert 0 <= stats['cpu_percent'] <= 100 * psutil.cpu_count()

    # Test memory stats
    assert isinstance(stats['memory'], dict)
    assert set(stats['memory'].keys()) == {'rss', 'vms', 'percent'}
    assert isinstance(stats['memory']['rss'], int)
    assert isinstance(stats['memory']['vms'], int)
    assert isinstance(stats['memory']['percent'], float)
    assert stats['memory']['rss'] > 0
    assert stats['memory']['vms'] > 0
    assert 0 <= stats['memory']['percent'] <= 100

    # Test disk stats
    assert isinstance(stats['disk'], dict)
    assert set(stats['disk'].keys()) == {'total', 'used', 'free', 'percent'}
    assert isinstance(stats['disk']['total'], int)
    assert isinstance(stats['disk']['used'], int)
    assert isinstance(stats['disk']['free'], int)
    assert isinstance(stats['disk']['percent'], float)
    assert stats['disk']['total'] > 0
    assert stats['disk']['used'] >= 0
    assert stats['disk']['free'] >= 0
    assert 0 <= stats['disk']['percent'] <= 100
    # Verify that used + free is less than or equal to total
    # (might not be exactly equal due to filesystem overhead)
    assert stats['disk']['used'] + stats['disk']['free'] <= stats['disk']['total']

    # Test I/O stats
    assert isinstance(stats['io'], dict)
    assert set(stats['io'].keys()) == {'read_bytes', 'write_bytes'}
    assert isinstance(stats['io']['read_bytes'], int)
    assert isinstance(stats['io']['write_bytes'], int)
    assert stats['io']['read_bytes'] >= 0
    assert stats['io']['write_bytes'] >= 0


def test_get_system_stats_stability():
    """Test that get_system_stats can be called multiple times without errors."""
    # Call multiple times to ensure stability
    for _ in range(3):
        stats = get_system_stats()
        assert isinstance(stats, dict)
        assert stats['cpu_percent'] >= 0
