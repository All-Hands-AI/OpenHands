
# Session Management

Socket.io is used as the underlying protocol for client server communication. This allows the event
handlers in the code to be somewhat separate from the connection management - so brief connection
interruptions are recoverable.

There are 3 main server side event handlers:

* `connect` - Invoked when a new connection to the server is established. (This may be via http or WebSocket)
* `oh_user_action` - Invoked when a connected client sends an event (such as a prompt for the Agent) -
   this is distinct from the `oh_event` sent from the server to the client.
* `disconnect` - Invoked when a connected client disconnects from the server.

## Disconnect
The (manager)[manager.py] manages connections and sessions. Each session may have zero or more connections
associated with it. When a session no longer has any
connections associated with it, after a set amount of time (determined by `config.sandbox.close_delay`),
the session and runtime are passivated (So will need to be rehydrated to continue.)
