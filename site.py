import http.server
import socketserver
import os.path
import sys

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if not '.' in os.path.basename(self.path):
            possible_name = self.path.strip('/') + '.html'
            if os.path.isfile(possible_name):
                self.path = possible_name

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

Handler = MyRequestHandler
server = socketserver.TCPServer(('0.0.0.0', 8000), Handler)
server.serve_forever()
