"""CLI entry point and scheduler for the Cambridge Lookup sync."""

import logging
import time
from datetime import UTC, datetime, timedelta

import click
from flask import Flask

from app.config import (
    CAMBRIDGE_UIS_API_KEY,
    CAMBRIDGE_UIS_API_SECRET,
    LOOKUP_API_URL,
)

logger = logging.getLogger(__name__)


def seconds_until_hour(hour: int, now: datetime | None = None) -> float:
    """Seconds until the next `hour` o'clock UTC."""
    now = now or datetime.now(UTC)
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def sync_once(dry_run: bool) -> None:
    from app.common.lookup import LookupClient, LookupError
    from app.services.users.sync import sync_users

    client = LookupClient(
        client_id=CAMBRIDGE_UIS_API_KEY,
        client_secret=CAMBRIDGE_UIS_API_SECRET,
        base_url=LOOKUP_API_URL,
    )
    try:
        report = sync_users(client, dry_run=dry_run)
    except LookupError as exc:
        raise click.ClickException(
            f'Lookup failed, nothing was written: {exc}') from exc

    click.echo('DRY RUN - nothing written' if dry_run else 'Applied')
    click.echo(f'  {report.summary()}')


def register_cli(app: Flask) -> None:
    @app.cli.command('sync-users')
    @click.option('--dry-run', is_flag=True,
                  help='Report what would change, write nothing.')
    @click.option('--daily', is_flag=True,
                  help='Stay running and sync once a day.')
    @click.option('--at', 'at_hour', default=3, show_default=True,
                  metavar='HOUR', help='Hour of day (UTC) for --daily.')
    def sync_users_command(dry_run: bool, daily: bool,
                           at_hour: int) -> None:
        """Reconcile the user table against the Cambridge Lookup directory."""
        if not daily:
            sync_once(dry_run)
            return

        logger.info('Sync scheduled daily at %02d:00 UTC', at_hour)
        while True:
            time.sleep(seconds_until_hour(at_hour))
            try:
                sync_once(dry_run)
            except Exception:
                # A Lookup outage must not kill the scheduler; try tomorrow.
                logger.exception('Scheduled sync failed')
