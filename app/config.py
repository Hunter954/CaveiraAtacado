import os
from dotenv import load_dotenv

load_dotenv()


def _normalize_database_url(url: str) -> str:
    if not url:
        return 'sqlite:///caveira_atacado.db'

    normalized = url.strip()

    if normalized.startswith('postgres://'):
        normalized = normalized.replace('postgres://', 'postgresql+psycopg://', 1)
    elif normalized.startswith('postgresql://') and '+psycopg' not in normalized:
        normalized = normalized.replace('postgresql://', 'postgresql+psycopg://', 1)

    return normalized


def _default_upload_folder() -> str:
    explicit = os.getenv('UPLOAD_FOLDER')
    if explicit:
        return explicit
    if os.path.isdir('/data'):
        return '/data/uploads'
    return 'app/static/uploads'


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.getenv('DATABASE_URL', 'sqlite:///caveira_atacado.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }
    UPLOAD_FOLDER = _default_upload_folder()
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))
    MERCADOPAGO_ACCESS_TOKEN = os.getenv('MERCADOPAGO_ACCESS_TOKEN', '')
    MERCADOPAGO_PUBLIC_KEY = os.getenv('MERCADOPAGO_PUBLIC_KEY', '')
    MERCADOPAGO_WEBHOOK_SECRET = os.getenv('MERCADOPAGO_WEBHOOK_SECRET', '')
    VIA_CEP_BASE_URL = os.getenv('VIA_CEP_BASE_URL', 'https://viacep.com.br/ws')
    DEFAULT_SHIPPING_PRICE = float(os.getenv('DEFAULT_SHIPPING_PRICE', '29.90'))
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 1025))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'no-reply@example.com')
    AUTO_CREATE_DB = os.getenv('AUTO_CREATE_DB', 'true').lower() == 'true'
    AUTO_SEED_DATA = os.getenv('AUTO_SEED_DATA', 'true').lower() == 'true'
