import http.server
import socketserver
import os
from pathlib import Path

def run_webserver():
    
    PORT = 8000

    file_path = Path(os.path.dirname(__file__))
    web_dir = os.path.join(os.getcwd(), 'visualization')
    os.chdir(web_dir)

    Handler = http.server.SimpleHTTPRequestHandler
    Handler.extensions_map.update({
        ".js": "application/javascript",
    })

    httpd = socketserver.TCPServer(("", PORT), Handler)
    httpd.serve_forever()

if __name__ == "__main__":

    run_webserver()