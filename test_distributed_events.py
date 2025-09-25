#!/usr/bin/env python3
"""Test distributed event broadcasting in Ray multi-worker implementation."""

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import List

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import ray
    from openhands.core.config import OpenHandsConfig
    from openhands.events import EventStream
    from openhands.events.event import Event, EventSource
    from openhands.events.stream import EventStreamSubscriber
    from openhands.events.action.message import MessageAction
    from openhands.llm.llm_registry import LLMRegistry
    from openhands.runtime.impl.ray.ray_runtime import RayRuntime
    from openhands.runtime.impl.ray.event_broadcaster import RayEventBroadcaster, RayEventStream
    
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


# Using MessageAction instead of MockEvent for proper event serialization


async def test_ray_event_broadcaster():
    """Test the Ray event broadcaster actor."""
    print("\n=== Testing Ray Event Broadcaster ===")
    
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    
    try:
        # Create broadcaster actor
        broadcaster = RayEventBroadcaster.remote()
        
        # Test health check
        health = ray.get(broadcaster.health_check.remote())
        if health.get('status') == 'healthy':
            print("✓ Broadcaster health check passed")
        else:
            print(f"✗ Broadcaster health check failed: {health}")
            return False
        
        # Test subscriber management
        success = ray.get(broadcaster.add_subscriber.remote("test_subscriber", "callback_1", "worker_1"))
        if success:
            print("✓ Added subscriber successfully")
        else:
            print("✗ Failed to add subscriber")
            return False
        
        # Test event broadcasting
        event_data = {
            'id': 1,
            'type': 'test_event',
            'message': 'Hello distributed world!',
            'timestamp': time.time()
        }
        
        result = ray.get(broadcaster.broadcast_event.remote(event_data, "test_source"))
        if result.get('success') and result.get('subscribers_notified') == 1:
            print(f"✓ Event broadcasted to {result['subscribers_notified']} subscribers")
        else:
            print(f"✗ Event broadcasting failed: {result}")
            return False
        
        # Test statistics
        stats = ray.get(broadcaster.get_subscriber_stats.remote())
        if stats.get('total_subscribers') == 1:
            print(f"✓ Subscriber statistics correct: {stats['total_subscribers']} subscribers")
        else:
            print(f"✗ Subscriber statistics incorrect: {stats}")
            return False
        
        # Test event history
        events = ray.get(broadcaster.get_recent_events.remote(5))
        if len(events) == 1 and events[0]['message'] == 'Hello distributed world!':
            print("✓ Event history working correctly")
        else:
            print(f"✗ Event history failed: {events}")
            return False
        
        # Test subscriber removal
        success = ray.get(broadcaster.remove_subscriber.remote("test_subscriber", "callback_1"))
        if success:
            print("✓ Removed subscriber successfully")
        else:
            print("✗ Failed to remove subscriber")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Ray event broadcaster test failed: {e}")
        return False


async def test_ray_event_stream():
    """Test the RayEventStream class."""
    print("\n=== Testing Ray Event Stream ===")
    
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    
    try:
        # Create event stream
        event_stream = RayEventStream("test_session")
        
        # Initialize
        await event_stream.initialize()
        print("✓ Ray event stream initialized")
        
        # Track received events
        received_events = []
        
        def test_callback(event: Event):
            received_events.append(getattr(event, 'content', 'no content'))
        
        # Subscribe to events
        event_stream.subscribe(
            EventStreamSubscriber.RUNTIME, 
            test_callback, 
            "test_callback"
        )
        print("✓ Subscribed to event stream")
        
        # Create and send test events using MessageAction
        test_events = [
            MessageAction(content="Event 1"),
            MessageAction(content="Event 2"), 
            MessageAction(content="Event 3")
        ]
        
        for event in test_events:
            event_stream.add_event(event, EventSource.USER)
        
        # Wait a bit for processing
        await asyncio.sleep(0.5)
        
        # Check statistics
        stats = await event_stream.get_stats()
        if isinstance(stats, dict) and stats.get('session_id') == 'test_session':
            print(f"✓ Event stream stats working: {stats.get('total_subscribers', 0)} subscribers")
        else:
            print(f"✗ Event stream stats failed: {stats}")
            return False
        
        # Check recent events
        recent = await event_stream.get_recent_events(5)
        if len(recent) >= 3:
            print(f"✓ Recent events working: {len(recent)} events retrieved")
        else:
            print(f"✗ Recent events failed: {recent}")
            return False
        
        # Unsubscribe
        event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, "test_callback")
        print("✓ Unsubscribed from event stream")
        
        # Cleanup
        event_stream.close()
        print("✓ Event stream closed")
        
        return True
        
    except Exception as e:
        print(f"✗ Ray event stream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_distributed_events_with_ray_runtime():
    """Test distributed events integration with RayRuntime."""
    print("\n=== Testing Distributed Events with RayRuntime ===")
    
    try:
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
        
        # Create runtime configuration
        config = OpenHandsConfig()
        
        # Mock event stream and LLM registry
        class MockEventStream:
            def subscribe(self, *args, **kwargs):
                pass
        
        # Create Ray runtime
        runtime = RayRuntime(
            config=config,
            event_stream=MockEventStream(),
            llm_registry=LLMRegistry(config),
            sid="distributed_test_session"
        )
        
        print("✓ Ray runtime created")
        
        # Connect to initialize distributed event streaming
        await runtime.connect()
        print("✓ Ray runtime connected with distributed events")
        
        # Track received events
        received_events = []
        
        def event_handler(event: Event):
            received_events.append(f"Received: {getattr(event, 'content', 'no content')}")
        
        # Subscribe to distributed events
        runtime.subscribe_to_distributed_events(
            EventStreamSubscriber.RUNTIME,
            event_handler,
            "test_handler"
        )
        print("✓ Subscribed to distributed events")
        
        # Get distributed event stats
        stats = await runtime.get_distributed_event_stats()
        if isinstance(stats, dict) and 'session_id' in stats:
            print(f"✓ Distributed event stats: {stats.get('total_subscribers', 0)} subscribers")
        else:
            print(f"✗ Distributed event stats failed: {stats}")
            runtime.close()
            return False
        
        # Create and broadcast test events using MessageAction
        for i in range(3):
            test_event = MessageAction(content=f"Runtime test event {i+1}")
            runtime.broadcast_event(test_event, EventSource.AGENT)
        
        # Wait for event processing
        await asyncio.sleep(1.0)
        
        # Get recent events
        recent_events = await runtime.get_recent_distributed_events(5)
        if len(recent_events) >= 3:
            print(f"✓ Recent distributed events: {len(recent_events)} events")
        else:
            print(f"✗ Recent distributed events failed: {recent_events}")
            runtime.close()
            return False
        
        # Unsubscribe from distributed events
        runtime.unsubscribe_from_distributed_events(
            EventStreamSubscriber.RUNTIME,
            "test_handler"
        )
        print("✓ Unsubscribed from distributed events")
        
        # Final stats check
        final_stats = await runtime.get_distributed_event_stats()
        print(f"✓ Final stats: {final_stats.get('total_subscribers', 0)} subscribers")
        
        # Cleanup
        runtime.close()
        print("✓ Runtime cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Distributed events with runtime test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_concurrent_event_broadcasting():
    """Test concurrent event broadcasting across multiple workers."""
    print("\n=== Testing Concurrent Event Broadcasting ===")
    
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    
    try:
        # Create multiple event streams simulating different workers
        event_streams = []
        for i in range(3):
            stream = RayEventStream(f"worker_session_{i}")
            await stream.initialize()
            event_streams.append(stream)
        
        print(f"✓ Created {len(event_streams)} event streams")
        
        # Track events across streams
        all_received_events = []
        
        def create_handler(worker_id: int):
            def handler(event: Event):
                all_received_events.append(f"Worker {worker_id}: {getattr(event, 'content', 'no content')}")
            return handler
        
        # Subscribe each stream
        for i, stream in enumerate(event_streams):
            stream.subscribe(
                EventStreamSubscriber.RUNTIME,
                create_handler(i),
                f"handler_{i}"
            )
        
        print("✓ All streams subscribed")
        
        # Broadcast events concurrently from different streams
        broadcast_tasks = []
        for i, stream in enumerate(event_streams):
            for j in range(2):
                event = MessageAction(content=f"Event from stream {i}, message {j+1}")
                task = asyncio.create_task(
                    asyncio.to_thread(stream.add_event, event, EventSource.AGENT)
                )
                broadcast_tasks.append(task)
        
        # Wait for all broadcasts to complete
        await asyncio.gather(*broadcast_tasks)
        print(f"✓ Completed {len(broadcast_tasks)} concurrent broadcasts")
        
        # Wait for event processing
        await asyncio.sleep(1.0)
        
        # Check that events were distributed
        total_events_broadcasted = 0
        for stream in event_streams:
            stats = await stream.get_stats()
            events = await stream.get_recent_events(10)
            total_events_broadcasted += len(events)
        
        if total_events_broadcasted >= 6:  # 3 streams * 2 events each
            print(f"✓ Concurrent broadcasting successful: {total_events_broadcasted} total events")
        else:
            print(f"✗ Concurrent broadcasting failed: only {total_events_broadcasted} events")
            return False
        
        # Cleanup all streams
        for stream in event_streams:
            stream.close()
        
        print("✓ All streams cleaned up")
        return True
        
    except Exception as e:
        print(f"✗ Concurrent event broadcasting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all distributed event tests."""
    print("🌐 Ray Distributed Event Broadcasting Testing")
    print("="*60)
    
    tests = [
        ("Ray Event Broadcaster", test_ray_event_broadcaster()),
        ("Ray Event Stream", test_ray_event_stream()),
        ("Distributed Events with Runtime", test_distributed_events_with_ray_runtime()),
        ("Concurrent Event Broadcasting", test_concurrent_event_broadcasting())
    ]
    
    results = []
    
    for name, test in tests:
        print(f"\n🧪 Running {name} test...")
        try:
            result = await test
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} test failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("🌐 DISTRIBUTED EVENT TESTING SUMMARY")
    print("="*60)
    
    passed = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} distributed event tests passed")
    
    if passed == len(results):
        print("🎉 All distributed event tests passed! Event streaming is working correctly.")
    else:
        print("⚠️  Some distributed event tests failed. Review event streaming implementation.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)