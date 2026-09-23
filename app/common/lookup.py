"""Client for the University of Cambridge Lookup/Ibis directory."""

import base64
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.common.timing import log_slow
from app.config import LOOKUP_API_URL, LOOKUP_SCOPE, LOOKUP_TOKEN_URL

logger = logging.getLogger(__name__)


class LookupError(Exception):
    """The directory could not be reached or did not answer usefully."""


@dataclass(frozen=True)
class LookupPerson:
    crsid: str
    name: str

    @property
    def email(self) -> str:
        return f'{self.crsid}@cam.ac.uk'


class LookupClient:
    """Reads group and institution membership from Lookup."""

    def __init__(self, client_id: str | None = None,
                 client_secret: str | None = None,
                 base_url: str = LOOKUP_API_URL, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._token: str | None = None
        self._token_expires_at = 0.0

    def _access_token(self) -> str:
        """Fetch (and cache) a client-credentials token."""
        if self._token and time.monotonic() < self._token_expires_at:
            return self._token

        body = urllib.parse.urlencode({
            'grant_type': 'client_credentials',
            'scope': LOOKUP_SCOPE,
        }).encode()
        basic = base64.b64encode(
            f'{self.client_id}:{self.client_secret}'.encode()
        ).decode()
        request = urllib.request.Request(LOOKUP_TOKEN_URL, data=body, headers={
            'Authorization': f'Basic {basic}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        })

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code in (400, 401):
                raise LookupError(
                    'The API Gateway rejected the credentials.'
                ) from exc
            raise LookupError(f'Token request failed: HTTP {exc.code}') from exc
        except urllib.error.URLError as exc:
            raise LookupError(f'Could not reach the API Gateway: {exc.reason}') from exc

        token = payload.get('access_token')
        if not token:
            raise LookupError('Token response contained no access_token')

        # Expire a minute early to avoid straddling the boundary.
        self._token = token
        self._token_expires_at = time.monotonic() + max(
            0, int(payload.get('expires_in', 3600)) - 60)
        return token

    def _get(self, path: str) -> dict[str, Any]:
        url = f'{self.base_url}/{path.lstrip("/")}'
        request = urllib.request.Request(url, headers={
            'Authorization': f'Bearer {self._access_token()}',
            'Accept': 'application/json',
        })
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise LookupError(f'Lookup has no such object: {path}') from exc
            raise LookupError(f'Lookup returned HTTP {exc.code} for {path}') from exc
        except urllib.error.URLError as exc:
            raise LookupError(f'Could not reach Lookup: {exc.reason}') from exc
        except json.JSONDecodeError as exc:
            raise LookupError(f'Lookup returned unparseable JSON: {exc}') from exc

    @staticmethod
    def _parse(payload: dict[str, Any]) -> list[LookupPerson]:
        people: list[LookupPerson] = []
        for person in (payload.get('result') or {}).get('people') or []:
            if person.get('cancelled'):
                continue

            identifier = person.get('identifier') or {}
            if identifier.get('scheme') != 'crsid':
                continue
            crsid = (identifier.get('value') or '').strip()
            if not crsid:
                continue

            # Fall back through other name fields.
            name = ''
            for key in ('visibleName', 'displayName', 'registeredName', 'surname'):
                if (person.get(key) or '').strip():
                    name = person[key].strip()
                    break

            people.append(LookupPerson(crsid=crsid, name=name or crsid))

        return people

    @log_slow(5.0)
    def members(self, lookup_name: str,
                lookup_type: str = 'group') -> list[LookupPerson]:
        """Members of a Lookup group or institution."""
        # TODO(khm39): this should probably be an enum
        if lookup_type not in ('group', 'inst'):
            raise ValueError(
                f"lookup_type must be 'group' or 'inst', got {lookup_type!r}")
        payload = self._get(f'{lookup_type}/{lookup_name}/members')
        people = self._parse(payload)
        logger.info('Lookup %s/%s returned %d current members',
                    lookup_type, lookup_name, len(people))
        return people
