#!/usr/bin/env python3
"""Test to demonstrate before/after fix behavior."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from openhands.runtime.utils import find_available_tcp_port
from openhands.runtime.utils.port_lock import find_available_port_with_lock


def test_without_locking():
    """Test port allocation without locking (simulates old behavior)."""
    print('=== Testing WITHOUT locking (old behavior) ===')

    allocated_ports = []

    def allocate_port_old_way():
        """Simulate the old port allocation method."""
        port = find_available_tcp_port(35000, 35010)
        allocated_ports.append(port)
        # Small delay to increase race condition chance
        time.sleep(0.01)
        return port

    # Run multiple workers concurrently
    num_workers = 10
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(allocate_port_old_way) for _ in range(num_workers)]
        results = [future.result() for future in as_completed(futures)]

    unique_ports = set(results)
    duplicates_found = len(results) != len(unique_ports)

    print(f'Total allocations: {len(results)}')
    print(f'Unique ports: {len(unique_ports)}')
    print(f'Allocated ports: {sorted(results)}')
    print(f'Duplicates found: {duplicates_found}')

    if duplicates_found:
        from collections import Counter

        counts = Counter(results)
        duplicates = {port: count for port, count in counts.items() if count > 1}
        print(f'Duplicate ports: {duplicates}')

    return duplicates_found


def test_with_locking():
    """Test port allocation with locking (new behavior)."""
    print('\n=== Testing WITH locking (new behavior) ===')

    allocated_ports = []
    port_locks = []

    def allocate_port_new_way():
        """Use the new port allocation method with locking."""
        result = find_available_port_with_lock(
            min_port=36000,
            max_port=36010,
            max_attempts=5,
            bind_address='0.0.0.0',
            lock_timeout=1.0,
        )

        if result:
            port, lock = result
            allocated_ports.append(port)
            port_locks.append(lock)
            # Same delay as old method
            time.sleep(0.01)
            return port
        return None

    # Run multiple workers concurrently
    num_workers = 10
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(allocate_port_new_way) for _ in range(num_workers)]
        results = [future.result() for future in as_completed(futures)]

    # Filter out None results
    successful_results = [r for r in results if r is not None]
    unique_ports = set(successful_results)
    duplicates_found = len(successful_results) != len(unique_ports)

    print(f'Total allocations: {len(successful_results)}')
    print(f'Unique ports: {len(unique_ports)}')
    print(f'Allocated ports: {sorted(successful_results)}')
    print(f'Duplicates found: {duplicates_found}')

    # Clean up locks
    for lock in port_locks:
        if lock:
            lock.release()

    return duplicates_found


def main():
    """Run both tests and compare results."""
    print('Testing port allocation race condition fix')
    print('=' * 50)

    # Test old behavior (should potentially show race conditions)
    old_has_duplicates = test_without_locking()

    # Test new behavior (should never have race conditions)
    new_has_duplicates = test_with_locking()

    print('\n' + '=' * 50)
    print('SUMMARY:')
    print(
        f'Old method (without locking): {"RACE CONDITION DETECTED" if old_has_duplicates else "No duplicates (race window too small)"}'
    )
    print(
        f'New method (with locking): {"RACE CONDITION DETECTED (BUG!)" if new_has_duplicates else "NO RACE CONDITIONS (FIXED!)"}'
    )

    if not new_has_duplicates:
        print('\n✅ Fix is working correctly - no race conditions with locking!')
    else:
        print('\n❌ Fix is not working - race conditions still present!')

    return not new_has_duplicates


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
