import os
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler


class MultiAddressServer(HTTPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


class LoggingHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(
            f'Request received: {self.address_string()} - {self.log_date_time_string()} - {format % args}'
        )


web_dir = os.path.join(os.path.dirname(__file__), 'static')
os.chdir(web_dir)
handler = LoggingHTTPRequestHandler

# Start the server
server = MultiAddressServer(('', 8000), handler)
print('Server running on http://localhost:8000 and http://127.0.0.1:8000')
server.serve_forever()
