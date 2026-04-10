import json
import mercadopago
from flask import current_app, url_for
from ..models import Payment
from ..extensions import db


class MercadoPagoService:
    def __init__(self):
        self.sdk = mercadopago.SDK(current_app.config['MERCADOPAGO_ACCESS_TOKEN'])

    def create_preference(self, order, payer_email):
        payload = {
            'items': [{
                'title': f'Pedido #{order.id} - Caveira Atacado',
                'quantity': 1,
                'currency_id': 'BRL',
                'unit_price': float(order.total_amount),
            }],
            'payer': {'email': payer_email},
            'external_reference': str(order.id),
            'notification_url': current_app.config['BASE_URL'] + url_for('webhooks.mercado_pago'),
            'back_urls': {
                'success': current_app.config['BASE_URL'] + url_for('checkout.confirmation', order_id=order.id),
                'failure': current_app.config['BASE_URL'] + url_for('checkout.confirmation', order_id=order.id),
                'pending': current_app.config['BASE_URL'] + url_for('checkout.confirmation', order_id=order.id),
            },
            'auto_return': 'approved'
        }
        result = self.sdk.preference().create(payload)
        response = result.get('response', {})
        payment = Payment(order_id=order.id, provider='mercado_pago', payment_type='checkout_pro', amount=order.total_amount, preference_id=response.get('id'), raw_response=json.dumps(response, ensure_ascii=False))
        db.session.add(payment)
        db.session.commit()
        return response


def update_payment_from_webhook(order, external_id, status, payload):
    payment = Payment.query.filter_by(order_id=order.id).first()
    if payment:
        payment.external_id = external_id
        payment.status = status
        payment.raw_response = json.dumps(payload, ensure_ascii=False)

    order.payment_status = status
    if status == 'approved':
        order.status = 'pago'
    elif status in {'pending', 'in_process'}:
        order.status = 'aguardando_pagamento'
    elif status in {'rejected', 'cancelled'}:
        order.status = 'cancelado'
    db.session.commit()
