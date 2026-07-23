#!/usr/bin/env python3
"""
Fillo Open & Click Tracking Server
Serves 1x1 transparent tracking pixels and click redirect URLs.
"""
import os
import json
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from email_analytics import (
    record_open_event,
    record_click_event,
    decode_email_token,
    PIXEL_GIF_BYTES
)

PORT = int(os.environ.get("TRACKING_PORT", 8080))

class TrackingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        client_ip = self.headers.get("X-Forwarded-For", self.client_address[0])
        user_agent = self.headers.get("User-Agent", "Unknown")

        # Open tracking pixel endpoint
        if path.startswith("/track/open"):
            token = query.get("id", [""])[0] or path.split("/")[-1].replace(".gif", "").replace(".png", "")
            if token:
                email_addr = decode_email_token(token)
                try:
                    record_open_event(email_addr, client_ip, user_agent)
                except Exception as e:
                    print(f"Open record error: {e}")

            # Return 1x1 transparent GIF
            self.send_response(200)
            self.send_header("Content-Type", "image/gif")
            self.send_header("Content-Length", str(len(PIXEL_GIF_BYTES)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(PIXEL_GIF_BYTES)

        # Click tracking redirect endpoint
        elif path.startswith("/track/click"):
            token = query.get("id", [""])[0] or path.split("/")[-1]
            target_url = query.get("target", ["https://t.me/Filloappbot"])[0]
            
            if token:
                email_addr = decode_email_token(token)
                try:
                    record_click_event(email_addr, target_url)
                except Exception as e:
                    print(f"Click record error: {e}")

            # Redirect 302 to target Telegram URL
            self.send_response(302)
            self.send_header("Location", target_url)
            self.end_headers()

        # Health check
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Fillo Tracking Server Online")

    def log_message(self, format, *args):
        # Silence routine GET HTTP logs to keep console clean
        return

def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, TrackingHandler)
    print(f"🚀 Fillo Tracking Server running on port {PORT}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
