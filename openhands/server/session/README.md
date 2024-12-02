
# Session Management

Socket.io is used as the underlying protocol for client server communication. This allows the event
handlers in the code to be somewhat separate from the connection management - so brief connection
interruptions are recoverable.

There are 3 main server side event handlers:

* `connect` - Invoked when a new connection to the server is established. (This may be via http or WebSocket)
* `oh_action` - Invoked when a connected client sends an event (Such as `INIT` or a prompt for the Agent) -
   this is distinct from the `oh_event` sent from the server to the client.
* `disconnect` - Invoked when a connected client disconnects from the server.

## Init
Each connection has a unique id, and when initially established, is not associated with any session. An
`INIT` event must be sent to the server in order to attach a connection to a session. The `INIT` event
may optionally include a GitHub token and a token to connect to an existing session. (Which may be running
locally or may need to be hydrated). If no token is received as part of the init event, it is assumed a
new session should be started.

## Disconnect
The (manager)[manager.py] manages connections and sessions. Each session may have zero or more connections
associated with it, managed by invocations of `INIT` and disconnect. When a session no longer has any
connections associated with it, after a set amount of time (determined by `config.sandbox.close_delay`),
the session and runtime are passivated (So will need to be rehydrated to continue.)
