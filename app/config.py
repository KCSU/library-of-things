import os

from dotenv import load_dotenv

load_dotenv()

def required_from_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f'Missing required environment variable: {key}')
    return value

# Flask client-side session cookie signing key
FLASK_SESSION_SECRET_KEY = required_from_env('FLASK_SESSION_SECRET_KEY')

# MySQL database connection configuration
MYSQL_HOST = required_from_env('MYSQL_HOST')
MYSQL_PORT = int(required_from_env('MYSQL_PORT'))
MYSQL_USERNAME = required_from_env('MYSQL_USERNAME')
MYSQL_PASSWORD = required_from_env('MYSQL_PASSWORD')
MYSQL_DATABASE = required_from_env('MYSQL_DATABASE')
MYSQL_DATABASE_URL = (
    f'mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}'
    f'@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
)
MYSQL_POOL_SIZE = 1
MYSQL_MAX_OVERFLOW = 1
MYSQL_POOL_TIMEOUT_SEC = 10
MYSQL_POOL_RECYCLE_SEC = 3600
MYSQL_POOL_PRE_PING = True

# Cambridge UIS API Access
CAMBRIDGE_UIS_API_KEY = required_from_env('CAMBRIDGE_UIS_API_KEY')
CAMBRIDGE_UIS_API_SECRET = required_from_env('CAMBRIDGE_UIS_API_SECRET')
LOOKUP_API_URL = os.getenv('LOOKUP_API_URL', 'https://api.apps.cam.ac.uk/lookup/v1')
LOOKUP_TOKEN_URL = 'https://api.apps.cam.ac.uk/oauth2/v1/token'
LOOKUP_SCOPE = 'https://api.apps.cam.ac.uk/lookup'

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

# Database image storage configuration
IMAGE_MAX_DIMENSION = 1200  # width, height
IMAGE_QUALITY = 80
IMAGE_CONTENT_TYPE = 'image/webp'
IMAGE_MAX_STORED_BYTES = 4 * 1024 * 1024  # 4 MiB
IMAGE_MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MiB
