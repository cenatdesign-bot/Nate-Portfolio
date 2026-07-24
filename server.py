#!/usr/bin/env python3
"""Static server for the Nataly Cetre portfolio (Railway)."""
import base64
import hmac
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("PORT", 3458))
HOST = "0.0.0.0" if os.environ.get("RAILWAY_ENVIRONMENT") else "127.0.0.1"

# Optional private gate. When PORTFOLIO_PASSWORD is set, the whole site
# requires HTTP Basic Auth so it stays visible only to whoever has the
# credentials. Username defaults to "nate" but can be overridden.
AUTH_USER = os.environ.get("PORTFOLIO_USER", "nate")
AUTH_PASSWORD = os.environ.get("PORTFOLIO_PASSWORD")
REALM = "Nataly Cetre Portfolio"

# Always serve this script's own folder, regardless of launch cwd.
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def _authorized(self):
        if not AUTH_PASSWORD:
            return True
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(header[6:]).decode("utf-8", "replace")
            user, _, password = decoded.partition(":")
        except Exception:
            return False
        # Constant-time compares to avoid leaking credentials via timing.
        return hmac.compare_digest(user, AUTH_USER) and hmac.compare_digest(
            password, AUTH_PASSWORD
        )

    def _require_auth(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", f'Basic realm="{REALM}"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Authentication required.")

    def do_GET(self):
        if not self._authorized():
            return self._require_auth()
        super().do_GET()

    def do_HEAD(self):
        if not self._authorized():
            return self._require_auth()
        super().do_HEAD()

    def list_directory(self, path):
        self.send_error(403, "Directory listing disabled")
        return None


if __name__ == "__main__":
    gated = "private (Basic Auth)" if AUTH_PASSWORD else "public"
    print(f"Serving portfolio on {HOST}:{PORT} [{gated}]", flush=True)
    HTTPServer((HOST, PORT), Handler).serve_forever()
