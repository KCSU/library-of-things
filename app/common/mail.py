"""Outgoing email, rendered from the plain-text templates in templates/email.

The first line of each template is 'Subject: ...' and the rest is the body.
"""

import logging
import smtplib
import ssl
import traceback
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import Any

from flask import current_app

from app.common import alerts
from app.config import SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USERNAME

logger = logging.getLogger(__name__)

_SMTP_TIMEOUT_SEC = 10
_SUBJECT_PREFIX = 'Subject: '
_SMTP_LOCAL_HOSTNAME = 'kcsu.org.uk'


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    body: str


def render(template: str, to: str, **context: Any) -> Email:
    """Render templates/email/<template>."""
    text = current_app.jinja_env.get_template(f'email/{template}').render(**context)
    first_line, _, body = text.partition('\n')
    if not first_line.startswith(_SUBJECT_PREFIX):
        raise ValueError(f'Email template {template} must start with a Subject line')
    return Email(to=to, subject=first_line.removeprefix(_SUBJECT_PREFIX), body=body)


def send(*emails: Email) -> int:
    """Send emails over a single connection, and return how many were accepted."""
    if not emails:
        return 0

    if not SMTP_HOST:
        for email in emails:
            logger.info(
                'SMTP_HOST unset, not sending to %s:\nSubject: %s\n%s',
                email.to,
                email.subject,
                email.body,
            )
        return 0

    sent = 0
    try:
        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            local_hostname=_SMTP_LOCAL_HOSTNAME,
            timeout=_SMTP_TIMEOUT_SEC,
        ) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if SMTP_USERNAME and SMTP_PASSWORD:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            for email in emails:
                try:
                    smtp.send_message(_to_message(email))
                    sent += 1
                except smtplib.SMTPException:
                    logger.exception('Could not send %r to %s', email.subject, email.to)
    except OSError:  # includes SMTPException
        logger.exception('SMTP session with %s:%d failed', SMTP_HOST, SMTP_PORT)
        alerts.send(
            'email-failed',
            f'Could not send {len(emails) - sent} of {len(emails)} emails',
            detail=traceback.format_exc(),
            smtp_host=SMTP_HOST,
        )

    logger.info('Sent %d of %d emails', sent, len(emails))
    return sent


def _to_message(email: Email) -> EmailMessage:
    message = EmailMessage()
    message['From'] = SMTP_FROM
    message['To'] = email.to
    message['Subject'] = email.subject
    message['Date'] = formatdate(localtime=True)
    message['Message-ID'] = make_msgid(domain=SMTP_FROM.rpartition('@')[2])
    message.set_content(email.body)
    return message
