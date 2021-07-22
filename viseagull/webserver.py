from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from os import path, getcwd, chdir

from pathlib import Path

def run_webserver():
    
    PORT = 8000

    file_path = Path(path.dirname(__file__))
    web_dir = path.join(getcwd(), 'visualization')
    chdir(web_dir)

    Handler = SimpleHTTPRequestHandler
    Handler.extensions_map.update({
        ".js": "application/javascript",
    })

    httpd = TCPServer(("", PORT), Handler)
    httpd.serve_forever()

if __name__ == "__main__":

    run_webserver()