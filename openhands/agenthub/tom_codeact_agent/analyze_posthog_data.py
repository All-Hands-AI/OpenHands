#!/usr/bin/env python3
"""
Simple PostHog Analyzer - Focus on Tom Agent Key Metrics

Tracks:
1. How many times people accept Tom consultations
2. If each session calls /sleeptime

Usage:
    export POSTHOG_PERSONAL_API_KEY=your_key
    python analyze_posthog_data.py
"""

import json
import os

import requests

from openhands.server.config.server_config import load_server_config

# Load .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not installed, skip


def analyze_tom_metrics():
    # Check API key
    personal_key = os.environ.get('POSTHOG_PERSONAL_API_KEY')
    if not personal_key:
        print('❌ Set POSTHOG_PERSONAL_API_KEY environment variable')
        print('Get it from: PostHog Settings → Personal API Keys')
        return

    # Setup
    load_server_config()
    headers = {'Authorization': f'Bearer {personal_key}'}
    base_url = 'https://us.i.posthog.com'

    # Get project ID from environment variable
    project_id = os.environ.get('PROJECT_ID')
    if not project_id:
        print('❌ PROJECT_ID environment variable is required')
        print('Set it with: export PROJECT_ID=your_project_id')
        return

    print(f'✅ Using project ID: {project_id}')

    # Use PostHog Query API with HogQL to get only Tom agent events
    query_payload = {
        'query': {
            'kind': 'HogQLQuery',
            'query': "SELECT event, properties, timestamp, distinct_id FROM events WHERE properties.component = 'tom_agent' AND timestamp >= now() - INTERVAL 7 DAY ORDER BY timestamp DESC",
        }
    }

    print('📥 Downloading Tom agent events using Query API...')
    response = requests.post(
        f'{base_url}/api/projects/{project_id}/query/',
        headers=headers,
        json=query_payload,
    )

    if response.status_code != 200:
        print(f'❌ Failed to get events: {response.status_code}')
        print(f'Response: {response.text}')
        return

    query_response = response.json()

    # Handle Query API response format
    if 'results' in query_response:
        tom_events = query_response['results']
    else:
        tom_events = []

    print(f'🤖 Tom agent events found: {len(tom_events)}')

    # Check if response was cached
    if query_response.get('is_cached'):
        print('📋 (Using cached results)')

    # Parse HogQL array format: [event, properties, timestamp, distinct_id]
    parsed_events = []
    for row in tom_events:
        if isinstance(row, list) and len(row) >= 4:
            try:
                properties = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                parsed_event = {
                    'event': row[0],
                    'properties': properties,
                    'timestamp': row[2],
                    'distinct_id': row[3],
                }
                parsed_events.append(parsed_event)
            except (json.JSONDecodeError, IndexError) as e:
                print(f'⚠️  Failed to parse event: {e}')
                continue

    tom_events = parsed_events
    print(f'✅ Parsed {len(tom_events)} Tom agent events')

    # Show event type breakdown for Tom events
    event_names: dict[str, int] = {}
    for event in tom_events:
        name = event.get('event', 'unknown_event')
        event_names[name] = event_names.get(name, 0) + 1

    print('🎯 Tom event types:')
    for name, count in sorted(event_names.items()):
        print(f'  {name}: {count}')

    # 1. CONSULTATION ACCEPTANCE ANALYSIS
    consultation_events = [
        e for e in tom_events if e['event'] == 'tom_consult_agent_interaction'
    ]

    if consultation_events:
        total_consultations = len(consultation_events)
        accepted = sum(
            1
            for e in consultation_events
            if e.get('properties', {}).get('accepted', 0) == 1
        )
        partially_accepted = sum(
            1
            for e in consultation_events
            if e.get('properties', {}).get('accepted', 0) == 0.5
        )
        rejected = sum(
            1
            for e in consultation_events
            if e.get('properties', {}).get('accepted', 0) == 0
        )

        acceptance_rate = (
            (accepted / total_consultations * 100) if total_consultations > 0 else 0
        )

        print('\n💬 CONSULTATION ANALYSIS:')
        print(f'  Total consultations: {total_consultations}')
        print(
            f'  ✅ Accepted: {accepted} ({accepted / total_consultations * 100:.1f}%)'
        )
        print(
            f'  ⚠️  Partially accepted: {partially_accepted} ({partially_accepted / total_consultations * 100:.1f}%)'
        )
        print(
            f'  ❌ Rejected: {rejected} ({rejected / total_consultations * 100:.1f}%)'
        )
        print(f'  📊 Overall acceptance rate: {acceptance_rate:.1f}%')
    else:
        print('\n💬 CONSULTATION ANALYSIS:')
        print('  No consultation events found')

    # 2. SLEEPTIME USAGE ANALYSIS
    sleeptime_events = [
        e for e in tom_events if e['event'] == 'tom_sleeptime_triggered'
    ]
    init_events = [e for e in tom_events if e['event'] == 'tom_agent_initialized']

    # Get unique users from both events
    sleeptime_users = set(e['distinct_id'] for e in sleeptime_events)
    total_users = set(e['distinct_id'] for e in init_events)

    print('\n⏰ SLEEPTIME USAGE ANALYSIS:')
    print(f'  Total sleeptime triggers: {len(sleeptime_events)}')
    print(f'  Users who used sleeptime: {len(sleeptime_users)}')
    print(f'  Total users: {len(total_users)}')

    if total_users:
        sleeptime_adoption_rate = len(sleeptime_users) / len(total_users) * 100
        print(f'  📊 Sleeptime adoption rate: {sleeptime_adoption_rate:.1f}%')

        if sleeptime_users:
            avg_sleeptime_per_user = len(sleeptime_events) / len(sleeptime_users)
            print(f'  📈 Avg sleeptime calls per user: {avg_sleeptime_per_user:.1f}')

    # 3. USER SESSION OVERVIEW
    print('\n👥 USER OVERVIEW:')
    print(f'  Total unique users: {len(total_users)}')
    print(
        f'  Users who consulted Tom: {len(set(e["distinct_id"] for e in consultation_events))}'
    )
    print(f'  Users who used sleeptime: {len(sleeptime_users)}')

    # 4. SIMPLE BREAKDOWN
    event_counts: dict[str, int] = {}
    for event in tom_events:
        event_name = event['event']
        event_counts[event_name] = event_counts.get(event_name, 0) + 1

    print('\n📋 ALL TOM EVENTS:')
    for event, count in sorted(event_counts.items()):
        print(f'  {event}: {count}')

    # Save detailed data
    with open('tom_metrics.json', 'w') as f:
        json.dump(
            {
                'consultation_metrics': {
                    'total_consultations': len(consultation_events),
                    'accepted': accepted if consultation_events else 0,
                    'partially_accepted': partially_accepted
                    if consultation_events
                    else 0,
                    'rejected': rejected if consultation_events else 0,
                    'acceptance_rate': acceptance_rate if consultation_events else 0,
                },
                'sleeptime_metrics': {
                    'total_triggers': len(sleeptime_events),
                    'unique_users': len(sleeptime_users),
                    'total_users': len(total_users),
                    'adoption_rate': sleeptime_adoption_rate if total_users else 0,
                },
                'raw_events': tom_events,
            },
            f,
            indent=2,
            default=str,
        )

    print('\n💾 Saved detailed metrics to tom_metrics.json')
    print('📅 Analysis period: Last 7 days')


if __name__ == '__main__':
    analyze_tom_metrics()
