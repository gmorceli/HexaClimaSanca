#!/usr/bin/env python3
"""Servidor web simples para servir o mapa de chuva."""

import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8080))
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.path = "/mapa_chuva_24h.html"
        return super().do_GET()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Servindo mapa em http://0.0.0.0:{PORT}")
    server.serve_forever()
