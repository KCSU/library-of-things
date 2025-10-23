#!/bin/bash -e

APP_DIR="/societies/kcsu/public_html/library-of-things"

# Activate Python virtual environment
. "$APP_DIR/venv/bin/activate"

# Run the app with gunicorn
# Using 2 workers and binding to a UNIX socket
cd "$APP_DIR"
exec gunicorn -w 2 -b "unix:$APP_DIR/web.sock" \
    --log-file - run:app
