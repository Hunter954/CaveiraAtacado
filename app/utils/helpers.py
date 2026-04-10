import re
from uuid import uuid4
from flask import session
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}


def slugify(value: str) -> str:
    value = re.sub(r'[^a-zA-Z0-9\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_filename(filename: str) -> str:
    ext = filename.rsplit('.', 1)[1].lower()
    base = secure_filename(filename.rsplit('.', 1)[0])
    return f'{base}-{uuid4().hex[:8]}.{ext}'


def get_or_create_session_id():
    if 'cart_session_id' not in session:
        session['cart_session_id'] = uuid4().hex
    return session['cart_session_id']
