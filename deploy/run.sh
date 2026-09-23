#!/bin/bash -e
APP_DIR="/societies/kcsu/library-of-things"
SOCKET="$APP_DIR/web.sock"

cd "$APP_DIR"
mkdir -p "$APP_DIR/logs"

exec "$APP_DIR/.venv/bin/gunicorn" -w 2 -b "unix:$SOCKET" --log-file - app.run:app
