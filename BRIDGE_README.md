# OpenHands Communication Bridge

En kraftig bridge som lar deg koble dine egne applikasjoner til OpenHands kommunikasjonskanaler.

## Hva gjør Bridge?

Bridge kobler seg på to hovedsignaler i OpenHands:

1. **Bruker Input** → OpenHands (når bruker skriver meldinger)
2. **OpenHands Output** → Bruker (når agent svarer eller utfører handlinger)

Dette lar deg:
- Overvåke all kommunikasjon mellom bruker og OpenHands
- Sende meldinger til OpenHands fra dine egne applikasjoner
- Bygge chatbots, monitoring-systemer, og integrasjoner
- Fungere både lokalt og i Docker-miljøer

## Rask Start

### 1. Grunnleggende bruk

```bash
# Installer avhengigheter
pip install python-socketio[asyncio] requests flask

# Kjør bridge
python openhands_bridge.py
```

### 2. Med konfigurasjon

```bash
# Opprett konfigurasjon
python bridge_docker_setup.py

# Kjør med config
python openhands_bridge.py --config bridge_config.json --daemon
```

### 3. Docker Setup

```bash
# Setup for Docker
python bridge_docker_setup.py

# Start med Docker Compose
docker-compose -f docker-compose.bridge.yml up -d
```

## Arkitektur

```
Dine Apps ←→ Bridge ←→ OpenHands ←→ Agent
     ↑                    ↑
     └── HTTP/WebSocket   └── WebSocket
```

### Signalflow

1. **Input**: `Bruker → WebSocket → oh_user_action → event_stream.add_event(USER)`
2. **Output**: `Agent → event_stream.add_event(AGENT) → sio.emit('oh_event') → WebSocket → Bruker`

Bridge kobler seg på begge disse punktene.

## API Referanse

### Bridge HTTP API

Bridge eksponerer en HTTP API på port 8888:

```bash
# Send melding til OpenHands
curl -X POST http://localhost:8888/send_message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hei OpenHands!", "type": "message"}'

# Sjekk status
curl http://localhost:8888/status
```

### WebSocket Events

Bridge sender events til registrerte handlers:

- `openhands_user_input` - Bruker input til OpenHands
- `openhands_agent_output` - Agent output fra OpenHands
- `openhands_error` - Feilmeldinger

## Handlers

Bridge bruker handlers for å behandle meldinger:

### LoggingBridgeHandler
Logger alle meldinger til fil:

```python
from openhands_bridge import OpenHandsBridge, LoggingBridgeHandler

bridge = OpenHandsBridge()
bridge.add_handler(LoggingBridgeHandler('/tmp/openhands.log'))
```

### WebSocketBridgeHandler
Sender meldinger til WebSocket server:

```python
from openhands_bridge import WebSocketBridgeHandler

handler = WebSocketBridgeHandler('ws://localhost:8889')
await handler.connect()
bridge.add_handler(handler)
```

### HTTPBridgeHandler
Sender meldinger til HTTP endpoints:

```python
from openhands_bridge import HTTPBridgeHandler

bridge.add_handler(HTTPBridgeHandler('http://localhost:8890'))
```

### Custom Handler
Lag din egen handler:

```python
from openhands_bridge import BridgeHandler, OpenHandsMessage

class MyHandler(BridgeHandler):
    async def handle_user_input(self, message: OpenHandsMessage):
        print(f"Bruker sa: {message.content}")

    async def handle_agent_output(self, message: OpenHandsMessage):
        print(f"Agent sa: {message.content}")

    async def handle_error(self, error: str, context: dict):
        print(f"Feil: {error}")

bridge.add_handler(MyHandler())
```

## Eksempler

### Enkel Chatbot

```python
from openhands_bridge import OpenHandsBridge, LoggingBridgeHandler

async def chatbot_demo():
    bridge = OpenHandsBridge()
    bridge.add_handler(LoggingBridgeHandler('/tmp/chatbot.log'))

    # Koble til samtale
    await bridge.connect_to_conversation("my-conversation")

    # Send melding
    await bridge.send_user_message("Hei! Kan du hjelpe meg med Python?")

    # Hold forbindelsen åpen
    await asyncio.sleep(60)
    await bridge.disconnect()

asyncio.run(chatbot_demo())
```

### Monitoring System

```python
from openhands_bridge import OpenHandsBridge, BridgeHandler

class MonitorHandler(BridgeHandler):
    def __init__(self):
        self.command_count = 0
        self.error_count = 0

    async def handle_agent_output(self, message):
        if message.content.get('action') == 'run':
            self.command_count += 1
            command = message.content.get('args', {}).get('command', '')
            print(f"Command #{self.command_count}: {command}")

    async def handle_error(self, error, context):
        self.error_count += 1
        print(f"Error #{self.error_count}: {error}")

bridge = OpenHandsBridge()
bridge.add_handler(MonitorHandler())
```

### Multi-App Integration

```python
# App 1: Chatbot
chatbot = OpenHandsBridge()
chatbot.add_handler(LoggingBridgeHandler('/tmp/chatbot.log'))

# App 2: Monitor
monitor = OpenHandsBridge()
monitor.add_handler(MonitorHandler())

# Begge kobler til samme conversation
await chatbot.connect_to_conversation("shared-conversation")
await monitor.connect_to_conversation("shared-conversation")
```

## Docker Integration

### Automatisk Setup

```bash
# Finn OpenHands containers og setup bridge
python bridge_docker_setup.py
```

Dette skriptet:
1. Finner kjørende OpenHands containers
2. Ekstraherer nettverksinformasjon
3. Tester forbindelser
4. Opprett konfigurasjonsfiler
5. Genererer Docker Compose setup

### Manuell Docker Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  openhands-bridge:
    build: .
    ports:
      - "8888:8888"
    environment:
      - OPENHANDS_URL=http://openhands:3000
    networks:
      - openhands-network
```

### Environment Variables

- `OPENHANDS_URL` - URL til OpenHands server
- `BRIDGE_PORT` - Port for HTTP API (default: 8888)
- `LOG_LEVEL` - Logging level (default: INFO)

## Konfigurasjon

### bridge_config.json

```json
{
  "openhands_urls": [
    "http://localhost:3000",
    "http://openhands:3000"
  ],
  "bridge_settings": {
    "auto_discover": true,
    "retry_attempts": 3,
    "retry_delay": 5,
    "log_level": "INFO"
  },
  "handlers": {
    "logging": {
      "enabled": true,
      "log_file": "/tmp/openhands_bridge.log"
    },
    "websocket": {
      "enabled": false,
      "url": "ws://localhost:8889"
    },
    "http": {
      "enabled": false,
      "url": "http://localhost:8888"
    }
  }
}
```

## Command Line Options

```bash
python openhands_bridge.py --help

Options:
  --url URL                 OpenHands URL
  --config FILE            Config file path
  --conversation-id ID     Conversation ID to connect to
  --server-port PORT       HTTP server port (default: 8888)
  --daemon                 Run as daemon
```

## Feilsøking

### Vanlige problemer

1. **Kan ikke finne OpenHands**
   ```bash
   # Sjekk at OpenHands kjører
   curl http://localhost:3000/api/health

   # Bruk spesifikk URL
   python openhands_bridge.py --url http://localhost:3000
   ```

2. **WebSocket forbindelse feiler**
   ```bash
   # Sjekk conversation ID
   python openhands_bridge.py --conversation-id "riktig-id"
   ```

3. **Docker networking issues**
   ```bash
   # Sjekk Docker nettverk
   docker network ls
   docker inspect openhands-network
   ```

### Debug Mode

```bash
# Aktiver debug logging
export LOG_LEVEL=DEBUG
python openhands_bridge.py --config bridge_config.json
```

### Logs

Bridge logger til flere steder:
- Console output
- `/tmp/openhands_bridge.log` (default)
- Handler-spesifikke logfiler

## Utvidelser

### Lag din egen Handler

```python
class DatabaseHandler(BridgeHandler):
    def __init__(self, db_connection):
        self.db = db_connection

    async def handle_user_input(self, message):
        # Lagre bruker input i database
        await self.db.execute(
            "INSERT INTO messages (type, content, timestamp) VALUES (?, ?, ?)",
            ('user_input', json.dumps(message.content), message.timestamp)
        )

    async def handle_agent_output(self, message):
        # Lagre agent output i database
        await self.db.execute(
            "INSERT INTO messages (type, content, timestamp) VALUES (?, ?, ?)",
            ('agent_output', json.dumps(message.content), message.timestamp)
        )
```

### Integrasjon med andre systemer

```python
# Slack integration
class SlackHandler(BridgeHandler):
    def __init__(self, slack_webhook):
        self.webhook = slack_webhook

    async def handle_error(self, error, context):
        # Send feil til Slack
        payload = {
            "text": f"OpenHands Error: {error}",
            "attachments": [{"text": json.dumps(context)}]
        }
        requests.post(self.webhook, json=payload)

# Email notifications
class EmailHandler(BridgeHandler):
    async def handle_agent_output(self, message):
        if 'error' in str(message.content).lower():
            # Send email ved feil
            send_email("admin@company.com", "OpenHands Error", str(message.content))
```

## Sikkerhet

### Autentisering

Bridge støtter samme autentisering som OpenHands:

```python
# Med API key
bridge = OpenHandsBridge("http://localhost:3000")
bridge.session_api_key = "your-api-key"

# Med cookies/headers
bridge.auth_headers = {"Authorization": "Bearer your-token"}
```

### Nettverk

- Bridge eksponerer HTTP API på port 8888
- Bruk reverse proxy for produksjon
- Konfigurer firewall regler

## Performance

### Optimalisering

- Bridge bruker asynkron I/O for høy ytelse
- Handlers kjører parallelt
- Automatisk reconnection ved forbindelsestap

### Monitoring

```python
# Overvåk bridge ytelse
class PerformanceHandler(BridgeHandler):
    def __init__(self):
        self.message_count = 0
        self.start_time = time.time()

    async def handle_user_input(self, message):
        self.message_count += 1

    async def handle_agent_output(self, message):
        self.message_count += 1

        # Log statistikk hver 100 meldinger
        if self.message_count % 100 == 0:
            elapsed = time.time() - self.start_time
            rate = self.message_count / elapsed
            logger.info(f"Processed {self.message_count} messages at {rate:.2f} msg/sec")
```

## Bidrag

Bridge er designet for å være utvidbar. Bidrag er velkomne:

1. Fork repository
2. Lag din feature branch
3. Implementer forbedringer
4. Skriv tester
5. Send pull request

## Lisens

Same som OpenHands - MIT License
