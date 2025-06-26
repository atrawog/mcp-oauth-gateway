#!/usr/bin/env python3
"""Simple HTTP server to receive OAuth callbacks using standard library only."""

import threading
import time
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from urllib.parse import parse_qs
from urllib.parse import urlparse


class CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    error = None

    def do_GET(self):
        """Handle GET request for OAuth callback."""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        if parsed_url.path == "/callback":
            if "error" in query_params:
                CallbackHandler.error = query_params["error"][0]
                response = f"❌ OAuth Error: {CallbackHandler.error}\n\nYou can close this window."
            elif "code" in query_params:
                CallbackHandler.auth_code = query_params["code"][0]
                response = f"✅ Authorization code received!\n\nCode: {CallbackHandler.auth_code[:10]}...\n\nYou can close this window."
            else:
                response = "❌ No authorization code received\n\nYou can close this window."
        else:
            response = "❌ Invalid callback path\n\nYou can close this window."

        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(response.encode())

    def log_message(self, format, *args):
        """Suppress log messages."""


def start_callback_server(port=8080):
    """Start callback server in a thread."""
    server = HTTPServer(("localhost", port), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print(f"🔗 Callback receiver started on http://localhost:{port}/callback")
    return server


def wait_for_callback(timeout=300):
    """Wait for OAuth callback."""
    print("⏳ Waiting for OAuth callback...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if CallbackHandler.auth_code or CallbackHandler.error:
            break
        time.sleep(1)

    if CallbackHandler.error:
        raise Exception(f"OAuth error: {CallbackHandler.error}")

    if not CallbackHandler.auth_code:
        raise Exception("Timeout waiting for OAuth callback")

    return CallbackHandler.auth_code


if __name__ == "__main__":
    server = start_callback_server()
    try:
        auth_code = wait_for_callback(30)
        print(f"Received code: {auth_code}")
    finally:
        server.shutdown()
