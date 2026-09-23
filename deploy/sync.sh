#!/bin/bash -e

APP_DIR="/societies/kcsu/library-of-things"

cd "$APP_DIR"
mkdir -p "$APP_DIR/logs"

exec "$APP_DIR/.venv/bin/flask" --app app.run sync-users --daily
