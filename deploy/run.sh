#!/bin/bash -e

APP_DIR="/societies/kcsu/public_html/library-of-things"

# Activate Python virtual environment
. "$APP_DIR/venv/bin/activate"

# Run the app with gunicorn
# Using 8 workers and binding to a UNIX socket
cd "$APP_DIR"
exec gunicorn -w 8 -b "unix:$APP_DIR/web.sock" \
    --umask=0007 --log-file - run:app