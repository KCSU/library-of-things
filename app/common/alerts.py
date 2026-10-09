"""Critical alerts, published to the kcsu-admin alerts pub/sub topic."""

import base64
import logging
import time

import google.auth
from google.auth.transport.requests import AuthorizedSession

from app.config import ALERTS_TOPIC
from app.proto.kcsu.alerts.v1.alert_pb2 import Alert

logger = logging.getLogger(__name__)

SOURCE = 'library-of-things'

_PUBSUB_SCOPE = 'https://www.googleapis.com/auth/pubsub'
_PUBLISH_TIMEOUT_SEC = 10

_session: AuthorizedSession | None = None


def send(dedup_key: str, summary: str, detail: str | None = None, **extra: str) -> None:
    """Raise an alert. Never raises: alerting must not take the app down with it.

    dedup_key names the problem, and stays the same each time it happens.
    """
    alert = Alert(
        source=SOURCE,
        dedup_key=dedup_key,
        occurred_at_unix=int(time.time()),
        summary=summary,
        detail=detail,
        extra=extra,
    )

    if not ALERTS_TOPIC:
        logger.warning('ALERTS_TOPIC unset, not publishing alert:\n%s', alert)
        return

    try:
        _publish(ALERTS_TOPIC, alert)
        logger.info('Published alert %r', dedup_key)
    except Exception:
        logger.exception('Could not publish alert %r', dedup_key)


def _publish(topic: str, alert: Alert) -> None:
    global _session
    if _session is None:
        credentials, _ = google.auth.default(scopes=[_PUBSUB_SCOPE])
        _session = AuthorizedSession(credentials)

    data = base64.b64encode(alert.SerializeToString()).decode('ascii')
    response = _session.post(
        f'https://pubsub.googleapis.com/v1/{topic}:publish',
        json={'messages': [{'data': data, 'attributes': {'source': SOURCE}}]},
        timeout=_PUBLISH_TIMEOUT_SEC,
    )
    response.raise_for_status()
