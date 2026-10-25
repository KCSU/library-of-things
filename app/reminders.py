"""CLI entry point for due and overdue loan reminders."""

import logging
import traceback
from datetime import date, datetime, timedelta

import click
from flask import Flask
from sqlalchemy.orm import selectinload

from app.common import alerts, mail
from app.common.timing import LONDON, london_today

logger = logging.getLogger(__name__)


def collect_reminders(today: date) -> list[mail.Email]:
    """One email per unreturned loan that is due today or overdue.

    Skips whichever of the two emails is turned off in the site settings.
    """
    from app.common.database import db_session
    from app.models import Loan
    from app.services.settings import service as settings_service

    enabled = settings_service.get_emails()
    if not (enabled['loan_due'] or enabled['loan_overdue']):
        logger.info('Due and overdue emails are turned off; nothing to send')
        return []

    tomorrow = datetime.combine(
        today + timedelta(days=1), datetime.min.time(), tzinfo=LONDON
    )
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
            days_overdue = (today - loan.due_date.astimezone(LONDON).date()).days
            email = 'loan_overdue' if days_overdue > 0 else 'loan_due'
            if not enabled[email]:
                continue
            emails.append(
                mail.render(
                    f'{email}.txt',
                    to=loan.user.email,
                    extra={
                        'user_id': str(loan.user_id),
                        'user_crsid': loan.user.crsid,
                        'item_id': str(loan.item_id),
                        'loan_id': str(loan.id),
                    },
                    loan=loan,
                    days_overdue=days_overdue,
                )
            )
        return emails


def remind_once(dry_run: bool) -> None:
    emails = collect_reminders(london_today())
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
    @click.option(
        '--alert',
        is_flag=True,
        help='Raise an alert if the reminders fail, for scheduled runs.',
    )
    def send_reminders_command(dry_run: bool, alert: bool) -> None:
        """Email borrowers whose loans are due today or overdue."""
        try:
            remind_once(dry_run)
        except Exception:
            if alert:
                alerts.send(
                    'reminder-job-failed',
                    'Daily loan reminders failed',
                    detail=traceback.format_exc(),
                )
            raise
