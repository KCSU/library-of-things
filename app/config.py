import os

import certifi
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv()


def required_from_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f'Missing required environment variable: {key}')
    return value

APP_VERSION = os.getenv('APP_VERSION', 'dev')

# Flask client-side session cookie signing key
FLASK_SESSION_SECRET_KEY = required_from_env('FLASK_SESSION_SECRET_KEY')

# Session cookie name.
SESSION_COOKIE_NAME = '__session'

# SQLAlchemy database URL.
DATABASE_URL = make_url(required_from_env('DATABASE_URL'))
if str(DATABASE_URL.query.get('sslmode', '')).startswith('verify') and (
    'sslrootcert' not in DATABASE_URL.query
):
    DATABASE_URL = DATABASE_URL.update_query_dict({'sslrootcert': certifi.where()})

DATABASE_POOL_SIZE = 1
DATABASE_MAX_OVERFLOW = 1
DATABASE_POOL_TIMEOUT_SEC = 10
DATABASE_POOL_RECYCLE_SEC = 3600
DATABASE_POOL_PRE_PING = True

# Lookup group members that are allowed to sign in.
LOOKUP_GROUPS = ('kings-sis-ug', 'kings-sis-pg')

# Leave unset to turn push endpoints off.
PUBSUB_PUSH_SERVICE_ACCOUNT = os.getenv('PUBSUB_PUSH_SERVICE_ACCOUNT')
PUBSUB_PUSH_AUDIENCE = os.getenv('PUBSUB_PUSH_AUDIENCE', 'library-of-things')

# Google OAuth2 configuration
GOOGLE_OAUTH2_CLIENT_ID = required_from_env('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = required_from_env('GOOGLE_OAUTH2_CLIENT_SECRET')
GOOGLE_API_BASE_URL = 'https://www.googleapis.com/oauth2/v1/'
GOOGLE_ACCESS_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_AUTHORIZE_URL = 'https://accounts.google.com/o/oauth2/v2/auth?hd=cam.ac.uk'
GOOGLE_SERVER_METADATA_URL = (
    'https://accounts.google.com/.well-known/openid-configuration'
)
GOOGLE_SCOPE = 'profile email openid'

# SMTP configuration. Leave SMTP_HOST unset to log emails instead of sending them.
SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(required_from_env('SMTP_PORT'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = required_from_env('SMTP_FROM')
ALERTS_TOPIC = os.getenv('ALERTS_TOPIC')

# Database image storage configuration
IMAGE_MAX_DIMENSION = 1200  # width, height
IMAGE_QUALITY = 80
IMAGE_CONTENT_TYPE = 'image/webp'
IMAGE_MAX_STORED_BYTES = 1024 * 1024  # 1 MiB
IMAGE_MAX_UPLOAD_BYTES = 24 * 1024 * 1024  # 24 MiB
