import os
from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(url: str) -> str:
    if not url:
        return 'sqlite:///caveira_atacado.db'

    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    scheme = url.split('://', 1)[0]
    if scheme == 'postgresql':
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)

    return url


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.getenv('DATABASE_URL', 'sqlite:///caveira_atacado.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
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
