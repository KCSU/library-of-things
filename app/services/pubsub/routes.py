"""Messages that Google Cloud Pub/Sub subscriptions push to the app."""

import base64
import logging
import traceback

from flask import Blueprint, request
from flask.typing import ResponseReturnValue
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.common import alerts
from app.config import PUBSUB_PUSH_AUDIENCE, PUBSUB_PUSH_SERVICE_ACCOUNT
from app.proto.kcsu.lookup.v1.group_snapshot_pb2 import GroupSnapshot
from app.services.users.sync import apply_snapshot

logger = logging.getLogger(__name__)

pubsub_bp = Blueprint('pubsub', __name__)


def _from_pubsub() -> bool:
    """Whether Google signed the request's token for our push service account."""
    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    if scheme != 'Bearer' or not token:
        return False
    try:
        claims = id_token.verify_oauth2_token(
            token, google_requests.Request(), audience=PUBSUB_PUSH_AUDIENCE
        )
    except ValueError:
        return False
    return (
        claims.get('email') == PUBSUB_PUSH_SERVICE_ACCOUNT
        and claims.get('email_verified') is True
    )


@pubsub_bp.route('/pubsub/lookup-group-members', methods=['POST'])
def lookup_group_members() -> ResponseReturnValue:
    """A GroupSnapshot from kcsu-admin's lookup-group-members topic."""
    if not PUBSUB_PUSH_SERVICE_ACCOUNT:
        return '', 404
    if not _from_pubsub():
        return '', 403

    try:
        snapshot = GroupSnapshot.FromString(
            base64.b64decode(request.get_json()['message']['data'], validate=True)
        )
    except Exception:
        # Redelivering can't fix a malformed message
        logger.exception('Dropping a malformed Lookup snapshot')
        alerts.send(
            'lookup-snapshot-malformed',
            'Dropped a malformed Lookup snapshot',
            detail=traceback.format_exc(),
        )
        return '', 204

    try:
        apply_snapshot(snapshot)
    except Exception:
        logger.exception('Lookup sync failed for %s', snapshot.name)
        alerts.send(
            'lookup-sync-failed',
            'Lookup sync failed',
            detail=traceback.format_exc(),
            lookup_group=snapshot.name,
        )
        return '', 500
    return '', 204
