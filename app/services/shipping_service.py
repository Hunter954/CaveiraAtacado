from flask import current_app
from .cep_service import lookup_cep


def calculate_shipping(zipcode: str):
    address = lookup_cep(zipcode)
    if address.get('error'):
        return address

    base = current_app.config['DEFAULT_SHIPPING_PRICE']
    state = address.get('uf', '')
    multiplier = 1.0 if state in {'SP', 'RJ', 'MG', 'ES'} else 1.35
    return {
        'zipcode': zipcode,
        'street': address.get('logradouro', ''),
        'neighborhood': address.get('bairro', ''),
        'city': address.get('localidade', ''),
        'state': state,
        'shipping_options': [
            {'method': 'Entrega Padrão', 'price': round(base * multiplier, 2), 'days': 6},
            {'method': 'Entrega Expressa', 'price': round((base + 14) * multiplier, 2), 'days': 2},
        ]
    }
