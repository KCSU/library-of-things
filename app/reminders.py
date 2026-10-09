"""CLI entry point and scheduler for due and overdue loan reminders."""

import logging
import time
import traceback
from datetime import date, datetime, timedelta

import click
from flask import Flask
from sqlalchemy.orm import selectinload

from app.common import alerts, mail
from app.lookup_sync import seconds_until_hour

logger = logging.getLogger(__name__)


def collect_reminders(today: date) -> list[mail.Email]:
    """One email per unreturned loan that is due today or overdue."""
    from app.common.database import db_session
    from app.models import Loan

    tomorrow = datetime.combine(today + timedelta(days=1), datetime.min.time())
    with db_session() as session:
        loans = (
            session.query(Loan)
            .filter(
                Loan.returned_at.is_(None),
                Loan.due_date.is_not(None),
                Loan.due_date < tomorrow,
            )
            .options(selectinload(Loan.item), selectinload(Loan.user))
            .all()
        )

        emails = []
        for loan in loans:
            assert loan.due_date is not None  # filtered above
            days_overdue = (today - loan.due_date.date()).days
            template = 'loan_overdue.txt' if days_overdue > 0 else 'loan_due.txt'
            emails.append(
                mail.render(
                    template, to=loan.user.email, loan=loan, days_overdue=days_overdue
                )
            )
        return emails


def remind_once(dry_run: bool) -> None:
    emails = collect_reminders(date.today())
    if dry_run:
        for email in emails:
            click.echo(f'  {email.to}: {email.subject}')
        click.echo(f'DRY RUN - {len(emails)} reminders, none sent')
        return

    sent = mail.send(*emails)
    click.echo(f'Sent {sent} of {len(emails)} reminders')


def register_cli(app: Flask) -> None:
    @app.cli.command('send-reminders')
    @click.option('--dry-run', is_flag=True, help='List the reminders, send nothing.')
    @click.option('--daily', is_flag=True, help='Stay running and remind once a day.')
    @click.option(
        '--at',
        'at_hour',
        default=2,
        show_default=True,
        metavar='HOUR',
        help='Hour of day (UTC) for --daily.',
    )
    def send_reminders_command(dry_run: bool, daily: bool, at_hour: int) -> None:
        """Email borrowers whose loans are due today or overdue."""
        if not daily:
            remind_once(dry_run)
            return

        logger.info('Reminders scheduled daily at %02d:00 UTC', at_hour)
        while True:
            time.sleep(seconds_until_hour(at_hour))
            try:
                remind_once(dry_run)
            except Exception:
                # A database or mail outage must not kill the scheduler.
                logger.exception('Scheduled reminders failed')
                alerts.send(
                    'reminder-job-failed',
                    'Daily loan reminders failed',
                    detail=traceback.format_exc(),
                )
