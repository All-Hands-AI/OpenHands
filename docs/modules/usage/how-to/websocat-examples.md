---
sidebar_position: 10
---

# WebSocket Testing with Websocat

This guide provides practical examples of using [websocat](https://github.com/vi/websocat) to interact with the OpenHands WebSocket API for testing and debugging purposes.

## What is Websocat?

Websocat is a command-line utility for interacting with WebSockets, similar to how `curl` is used for HTTP requests. It allows you to:

- Connect to WebSocket servers
- Send and receive WebSocket messages
- Test WebSocket APIs without writing code

## Installation

### macOS

```bash
brew install websocat
```

### Linux

```bash
curl -L https://github.com/vi/websocat/releases/download/v1.11.0/websocat.x86_64-unknown-linux-musl > websocat
chmod +x websocat
sudo mv websocat /usr/local/bin/
```

### Windows

Download the latest release from the [GitHub releases page](https://github.com/vi/websocat/releases) and add it to your PATH.

## Basic Usage with OpenHands

### Connecting to the WebSocket

To connect to the OpenHands WebSocket API:

```bash
websocat "ws://your-openhands-server/socket.io/?EIO=4&transport=websocket&conversation_id=your-conversation-id&latest_event_id=-1"
```

This will establish a connection and display all incoming messages. The Socket.IO protocol sends some initial messages:

```
0{"sid":"...","upgrades":[],"pingInterval":25000,"pingTimeout":20000}
```

### Understanding Socket.IO Protocol

Socket.IO messages follow this format:

- `0` - Socket.IO handshake
- `2` - Ping
- `3` - Pong
- `40` - Connection established
- `42["event_name", {...}]` - Event with data

### Sending a User Message

To send a message to the agent:

```bash
echo '42["oh_user_action",{"type":"message","source":"user","message":"Hello, agent!"}]' | \
websocat "ws://your-openhands-server/socket.io/?EIO=4&transport=websocket&conversation_id=your-conversation-id&latest_event_id=-1"
```

## Practical Examples

### 1. Establishing a Persistent Connection

```bash
websocat -v "ws://your-openhands-server/socket.io/?EIO=4&transport=websocket&conversation_id=your-conversation-id&latest_event_id=-1"
```

The `-v` flag enables verbose output, showing both sent and received messages.

### 2. Sending a Message and Viewing the Response

Create a file named `message.txt` with the following content:

```
42["oh_user_action",{"type":"message","source":"user","message":"Can you help me with my project?"}]
```

Then send it:

```bash
cat message.txt | websocat "ws://your-openhands-server/socket.io/?EIO=4&transport=websocket&conversation_id=your-conversation-id&latest_event_id=-1"
```

### 3. Interactive Session

For an interactive session where you can type messages:

```bash
websocat -t "ws://your-openhands-server/socket.io/?EIO=4&transport=websocket&conversation_id=your-conversation-id&latest_event_id=-1"
```

Then you can type messages in the format:

```
42["oh_user_action",{"type":"message","source":"user","message":"Your message here"}]
```

### 4. Filtering Events

To filter and display only agent messages:

```bash
websocat "ws://your-openhands-server/socket.io/?EIO=4&transport=websocket&conversation_id=your-conversation-id&latest_event_id=-1" | \
grep -o '42\["oh_event",{.*"source":"agent".*}\]'
```

### 5. Saving Events to a File

To save all events to a file for later analysis:

```bash
websocat "ws://your-openhands-server/socket.io/?EIO=4&transport=websocket&conversation_id=your-conversation-id&latest_event_id=-1" > events.log
```

### 6. Replaying a Sequence of Actions

Create a file with multiple actions:

```
# actions.txt
42["oh_user_action",{"type":"message","source":"user","message":"Hello"}]
42["oh_user_action",{"type":"message","source":"user","message":"Can you list the files in the current directory?"}]
42["oh_user_action",{"type":"message","source":"user","message":"What's in the README.md file?"}]
```

Then send them sequentially:

```bash
cat actions.txt | websocat --no-close "ws://your-openhands-server/socket.io/?EIO=4&transport=websocket&conversation_id=your-conversation-id&latest_event_id=-1"
```

## Advanced Usage

### Using JSON Templates

You can create JSON templates for common actions:

```bash
# Create a template
cat > message_template.json << EOF
{
  "type": "message",
  "source": "user",
  "message": "PLACEHOLDER"
}
EOF

# Use the template
MESSAGE="Can you explain how the websocket API works?"
cat message_template.json | sed "s/PLACEHOLDER/$MESSAGE/" | \
jq -c . | xargs -I{} echo '42["oh_user_action",{}]' | \
websocat "ws://your-openhands-server/socket.io/?EIO=4&transport=websocket&conversation_id=your-conversation-id&latest_event_id=-1"
```

### Handling Pings

Socket.IO requires responding to ping messages with pong messages. This script handles that automatically:

```bash
#!/bin/bash
# websocket_client.sh

CONVERSATION_ID="your-conversation-id"
SERVER="your-openhands-server"

# Function to send a pong in response to a ping
handle_ping() {
  while read -r line; do
    echo "$line"
    if [[ "$line" == "2"* ]]; then
      echo "3"
    fi
  done
}

# Connect to the WebSocket and handle pings
websocat "ws://$SERVER/socket.io/?EIO=4&transport=websocket&conversation_id=$CONVERSATION_ID&latest_event_id=-1" | handle_ping
```

Make the script executable and run it:

```bash
chmod +x websocket_client.sh
./websocket_client.sh
```

## Troubleshooting

### Connection Issues

If you're having trouble connecting:

```bash
# Check if the server is reachable
ping your-openhands-server

# Test with verbose output
websocat -v "ws://your-openhands-server/socket.io/?EIO=4&transport=websocket&conversation_id=your-conversation-id&latest_event_id=-1"
```

### Protocol Errors

If you're seeing protocol errors:

1. Ensure you're using the correct Socket.IO protocol version (EIO=4)
2. Verify that your message format follows the Socket.IO protocol
3. Check that your JSON is valid

## Conclusion

Websocat is a powerful tool for testing and debugging WebSocket connections. By using the examples in this guide, you can interact with the OpenHands WebSocket API directly from the command line, which is useful for:

- Testing new features
- Debugging connection issues
- Automating interactions with the OpenHands agent
- Learning how the WebSocket API works

For more information about the WebSocket API itself, see the [WebSocket API Reference](../architecture/websocket-api.md) and [Connecting to the WebSocket](./websocket-connection.md) guides.