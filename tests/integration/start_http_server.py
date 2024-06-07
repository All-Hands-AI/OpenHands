import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

web_dir = os.path.join(os.path.dirname(__file__), 'static')
os.chdir(web_dir)
handler = SimpleHTTPRequestHandler

# Start the server
server = HTTPServer(('localhost', 8000), handler)
server.serve_forever()
