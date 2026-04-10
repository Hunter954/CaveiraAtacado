import requests
from flask import current_app


def lookup_cep(zipcode: str):
    sanitized = ''.join(filter(str.isdigit, zipcode or ''))
    if len(sanitized) != 8:
        return {'error': 'CEP inválido.'}

    url = f"{current_app.config['VIA_CEP_BASE_URL'].rstrip('/')}/{sanitized}/json/"
    response = requests.get(url, timeout=10)
    data = response.json()
    if data.get('erro'):
        return {'error': 'CEP não encontrado.'}
    return data
