#!/usr/bin/env python3
"""Static server for the Nataly Cetre portfolio (Railway)."""
import base64
import hmac
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("PORT", 3458))
IS_PRODUCTION = bool(os.environ.get("RAILWAY_ENVIRONMENT"))
HOST = "0.0.0.0" if IS_PRODUCTION else "127.0.0.1"

# Two independent gates:
#
# 1. PORTFOLIO_PASSWORD — when set, the WHOLE site requires HTTP Basic Auth
#    (native browser prompt). Use this to keep everything private. Username
#    defaults to "nate".
# 2. CASE_STUDY_PASSWORD — when set (and PORTFOLIO_PASSWORD is NOT), the site
#    is public but the detailed case-study JSON files stay locked. The front-end
#    collects the password and sends it as `Authorization: Basic <b64 user:pass>`
#    on those fetches. Teaser data (projects.json, covers) stays public so the
#    work grid still renders. This is the "public portfolio, private case
#    studies" mode.
AUTH_USER = os.environ.get("PORTFOLIO_USER", "nate")
AUTH_PASSWORD = os.environ.get("PORTFOLIO_PASSWORD")
CASE_STUDY_PASSWORD = os.environ.get("CASE_STUDY_PASSWORD")
REALM = "Nataly Cetre Portfolio"

# Source/config files that should never be served to visitors. Matched by
# basename; any dotfile is blocked too.
BLOCKED_NAMES = {"server.py", "procfile", "readme.md", "deploy.sh"}

# Always serve this script's own folder, regardless of launch cwd.
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        if IS_PRODUCTION:
            self.send_header(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
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

    def _basic_password(self):
        """The password from an Authorization: Basic header, or None."""
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return None
        try:
            decoded = base64.b64decode(header[6:]).decode("utf-8", "replace")
            _user, _, password = decoded.partition(":")
            return password
        except Exception:
            return None

    def _is_case_study_detail(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        name = path.rsplit("/", 1)[-1].lower()
        return name.startswith("case-study-") and name.endswith(".json")

    def _case_study_authorized(self):
        supplied = self._basic_password()
        if supplied is None:
            return False
        return hmac.compare_digest(supplied, CASE_STUDY_PASSWORD)

    def _is_blocked(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        parts = [p for p in path.split("/") if p]
        if any(p.startswith(".") for p in parts):
            return True
        name = parts[-1].lower() if parts else ""
        return name in BLOCKED_NAMES

    def _guard(self):
        # Returns True if the request was handled (blocked/unauthorized).
        if AUTH_PASSWORD:
            # Whole-site gate (native Basic Auth prompt).
            if not self._authorized():
                self._require_auth()
                return True
        elif CASE_STUDY_PASSWORD and self._is_case_study_detail():
            # Case-study gate. Silent 401 (no WWW-Authenticate) so the browser
            # never shows its own dialog — the site's own unlock UI handles it.
            if not self._case_study_authorized():
                self.send_error(401, "Case study locked")
                return True
        if self._is_blocked():
            self.send_error(404, "Not found")
            return True
        return False

    def do_GET(self):
        if self._guard():
            return
        super().do_GET()

    def do_HEAD(self):
        if self._guard():
            return
        super().do_HEAD()

    def list_directory(self, path):
        self.send_error(403, "Directory listing disabled")
        return None


if __name__ == "__main__":
    # Fail closed in production: never expose the site unprotected because an
    # env var went missing. Local dev (no RAILWAY_ENVIRONMENT) stays open.
    if IS_PRODUCTION and not AUTH_PASSWORD:
        sys.exit(
            "Refusing to start: PORTFOLIO_PASSWORD is not set in production. "
            "Set it (private) or intentionally run locally to serve unprotected."
        )
    gated = "private (Basic Auth)" if AUTH_PASSWORD else "public"
    print(f"Serving portfolio on {HOST}:{PORT} [{gated}]", flush=True)
    HTTPServer((HOST, PORT), Handler).serve_forever()
