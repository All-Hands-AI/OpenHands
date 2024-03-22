## Simple HTTP Server

This server is a basic HTTP server written in Python. It serves content on two paths:

- `/` responds with `Hello World`
- `/test` responds with a simple HTML page containing a `<h1>` tag with `Test Page`.

### Running the Server
To run the server, use the following command:

```
python3 server.py
```

The server will start on port 8000. You can access it by navigating to `http://localhost:8000` for the Hello World message or `http://localhost:8000/test` for the test page.

### Stopping the Server
To stop the server, you will need to kill the process manually. If you started the server in the background using this environment, use the `kill` action with the correct process ID.

### Modifications
This server has been modified to handle requests to different paths, demonstrating basic routing capabilities.

### Future Improvements
- Implement error handling for unexpected paths more gracefully.
- Optimize server performance for handling simultaneous requests.
- Add logging functionality for monitoring and debugging purposes.
