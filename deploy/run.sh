#!/bin/bash -e

APP_DIR="/societies/kcsu/public_html/library-of-things"

# Activate Python virtual environment.
cd "$APP_DIR"
. ".venv/bin/activate"

# Nightly Lookup sync.
mkdir -p "$APP_DIR/logs"
STAMP="$(date +%Y%m%d-%H%M%S)"
flask --app app.run sync-users --daily >> "$APP_DIR/logs/sync-$STAMP.log" 2>&1 &
SCHEDULER_PID=$!
echo "Lookup sync scheduler started (pid $SCHEDULER_PID)"

# Stop the scheduler whenever gunicorn stops.
trap 'kill "$SCHEDULER_PID" 2>/dev/null || true' EXIT INT TERM

# Run the app with gunicorn.
gunicorn -w 2 -b "unix:$APP_DIR/web.sock" \
    --log-file "$APP_DIR/logs/gunicorn-$STAMP.log" app.run:app
