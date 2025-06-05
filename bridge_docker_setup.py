#!/usr/bin/env python3
"""
Docker Setup for OpenHands Bridge

Dette skriptet setter opp bridge for å fungere med OpenHands i Docker
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def check_docker():
    """Sjekk om Docker er tilgjengelig"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f'✓ Docker found: {result.stdout.strip()}')
            return True
    except FileNotFoundError:
        pass

    print('✗ Docker not found')
    return False


def find_openhands_containers():
    """Finn OpenHands containers"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.ID}}\t{{.Names}}\t{{.Ports}}\t{{.Image}}'],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return []

        containers = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) >= 4:
                container_id, name, ports, image = parts[:4]

                # Sjekk om det er en OpenHands container
                if any(
                    keyword in name.lower() or keyword in image.lower()
                    for keyword in ['openhands', 'opendevin', 'devin']
                ):
                    containers.append(
                        {
                            'id': container_id,
                            'name': name,
                            'ports': ports,
                            'image': image,
                        }
                    )

        return containers

    except Exception as e:
        print(f'Error finding containers: {e}')
        return []


def get_container_network_info(container_id):
    """Få nettverksinformasjon for en container"""
    try:
        result = subprocess.run(
            [
                'docker',
                'inspect',
                container_id,
                '--format',
                '{{json .NetworkSettings}}',
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            network_info = json.loads(result.stdout.strip())
            return network_info

    except Exception as e:
        print(f'Error getting network info: {e}')

    return None


def extract_openhands_urls(containers):
    """Ekstraher mulige URLs for OpenHands"""
    urls = []

    for container in containers:
        # Fra ports mapping
        ports = container['ports']
        if ports:
            # Parse port mappings som "0.0.0.0:3000->3000/tcp"
            for port_mapping in ports.split(','):
                port_mapping = port_mapping.strip()
                if '->' in port_mapping and '3000' in port_mapping:
                    # Ekstraher host port
                    host_part = port_mapping.split('->')[0]
                    if ':' in host_part:
                        host_port = host_part.split(':')[-1]
                        urls.append(f'http://localhost:{host_port}')

        # Fra network info
        network_info = get_container_network_info(container['id'])
        if network_info:
            networks = network_info.get('Networks', {})
            for network_name, network_data in networks.items():
                ip_address = network_data.get('IPAddress')
                if ip_address:
                    urls.append(f'http://{ip_address}:3000')

    return list(set(urls))  # Remove duplicates


def test_openhands_connection(url):
    """Test forbindelse til OpenHands"""
    try:
        import requests

        response = requests.get(f'{url}/api/health', timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def create_bridge_config(openhands_urls):
    """Opprett konfigurasjonsfil for bridge"""
    config = {
        'openhands_urls': openhands_urls,
        'bridge_settings': {
            'auto_discover': True,
            'retry_attempts': 3,
            'retry_delay': 5,
            'log_level': 'INFO',
        },
        'handlers': {
            'logging': {'enabled': True, 'log_file': '/tmp/openhands_bridge.log'},
            'websocket': {'enabled': False, 'url': 'ws://localhost:8889'},
            'http': {'enabled': False, 'url': 'http://localhost:8888'},
        },
    }

    config_path = Path('bridge_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f'✓ Bridge config created: {config_path}')
    return config_path


def create_docker_compose():
    """Opprett docker-compose.yml for bridge"""
    compose_content = """version: '3.8'

services:
  openhands-bridge:
    build:
      context: .
      dockerfile: Dockerfile.bridge
    container_name: openhands-bridge
    ports:
      - "8888:8888"  # HTTP API
      - "8889:8889"  # WebSocket
    volumes:
      - ./bridge_logs:/tmp/logs
      - ./bridge_config.json:/app/bridge_config.json
    environment:
      - OPENHANDS_URL=http://openhands:3000
    networks:
      - openhands-network
    depends_on:
      - openhands
    restart: unless-stopped

networks:
  openhands-network:
    external: true
"""

    with open('docker-compose.bridge.yml', 'w') as f:
        f.write(compose_content)

    print('✓ Docker Compose file created: docker-compose.bridge.yml')


def create_dockerfile():
    """Opprett Dockerfile for bridge"""
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.bridge.txt .
RUN pip install -r requirements.bridge.txt

# Copy bridge files
COPY openhands_bridge.py .
COPY example_bridge_app.py .
COPY bridge_config.json .

# Create logs directory
RUN mkdir -p /tmp/logs

# Expose ports
EXPOSE 8888 8889

# Run bridge
CMD ["python", "openhands_bridge.py"]
"""

    with open('Dockerfile.bridge', 'w') as f:
        f.write(dockerfile_content)

    print('✓ Dockerfile created: Dockerfile.bridge')


def create_requirements():
    """Opprett requirements.txt for bridge"""
    requirements = """python-socketio[asyncio]>=5.8.0
requests>=2.28.0
flask>=2.3.0
aiohttp>=3.8.0
"""

    with open('requirements.bridge.txt', 'w') as f:
        f.write(requirements)

    print('✓ Requirements file created: requirements.bridge.txt')


def create_startup_script():
    """Opprett oppstartsskript"""
    script_content = """#!/bin/bash

# OpenHands Bridge Startup Script

echo "Starting OpenHands Bridge..."

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    OPENHANDS_URL=${OPENHANDS_URL:-"http://openhands:3000"}
else
    echo "Running on host system"
    OPENHANDS_URL=${OPENHANDS_URL:-"http://localhost:3000"}
fi

echo "OpenHands URL: $OPENHANDS_URL"

# Start bridge
python openhands_bridge.py --url "$OPENHANDS_URL" --config bridge_config.json
"""

    script_path = Path('start_bridge.sh')
    with open(script_path, 'w') as f:
        f.write(script_content)

    # Make executable
    os.chmod(script_path, 0o755)

    print(f'✓ Startup script created: {script_path}')


def main():
    """Hovedfunksjon"""
    print('OpenHands Bridge Docker Setup')
    print('=' * 40)

    # Sjekk Docker
    if not check_docker():
        print('\nPlease install Docker first:')
        print('https://docs.docker.com/get-docker/')
        return 1

    # Finn OpenHands containers
    print('\nLooking for OpenHands containers...')
    containers = find_openhands_containers()

    if not containers:
        print('✗ No OpenHands containers found')
        print('\nMake sure OpenHands is running in Docker:')
        print('docker run -it --rm -p 3000:3000 ghcr.io/all-hands-ai/openhands:main')
        return 1

    print(f'✓ Found {len(containers)} OpenHands container(s):')
    for container in containers:
        print(f'  - {container["name"]} ({container["id"][:12]})')

    # Ekstraher URLs
    print('\nExtracting OpenHands URLs...')
    urls = extract_openhands_urls(containers)

    if not urls:
        print('✗ Could not extract URLs from containers')
        return 1

    # Test forbindelser
    print('\nTesting connections...')
    working_urls = []
    for url in urls:
        if test_openhands_connection(url):
            print(f'✓ {url} - OK')
            working_urls.append(url)
        else:
            print(f'✗ {url} - Failed')

    if not working_urls:
        print('✗ No working OpenHands URLs found')
        return 1

    # Opprett filer
    print('\nCreating bridge files...')
    create_bridge_config(working_urls)
    create_docker_compose()
    create_dockerfile()
    create_requirements()
    create_startup_script()

    # Opprett logs directory
    os.makedirs('bridge_logs', exist_ok=True)
    print('✓ Logs directory created: bridge_logs/')

    print('\n' + '=' * 40)
    print('Setup complete!')
    print('\nTo start the bridge:')
    print('1. Local: ./start_bridge.sh')
    print('2. Docker: docker-compose -f docker-compose.bridge.yml up -d')
    print('\nBridge will be available at:')
    print('- HTTP API: http://localhost:8888')
    print('- WebSocket: ws://localhost:8889')

    return 0


if __name__ == '__main__':
    sys.exit(main())
