# Railway builds this instead of auto-detecting with Railpack. Railpack began
# emitting a RAILWAY_GIT_REPO_OWNER build secret that CLI upload deploys cannot
# supply, which failed every `railway up` from 2026-08-11. server.py is stdlib
# only, so a plain Python base image is all this needs.
FROM python:3.13-slim

WORKDIR /app
COPY . .

# server.py reads PORT from the environment (Railway sets it), binds 0.0.0.0
# whenever RAILWAY_ENVIRONMENT is present, and refuses to start in production
# without PORTFOLIO_PASSWORD. Mirrors the Procfile.
CMD ["python3", "server.py"]
