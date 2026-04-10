import json
import os
from decimal import Decimal
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .extensions import db
from .models import User, Category, Product, ProductImage, Cart, CartItem, Coupon, Order, OrderItem, UserAddress, PasswordReset, OrderStatusLog
from .services.shipping_service import calculate_shipping
from .services.cep_service import lookup_cep
from .services.payment_service import MercadoPagoService, update_payment_from_webhook
from .services.email_service import send_email
from .utils.helpers import get_or_create_session_id

core_bp = Blueprint('core', __name__)
auth_bp = Blueprint('auth', __name__)
shop_bp = Blueprint('shop', __name__)
cart_bp = Blueprint('cart', __name__)
checkout_bp = Blueprint('checkout', __name__)
user_bp = Blueprint('user', __name__)
webhook_bp = Blueprint('webhooks', __name__)


def get_cart():
    session_id = get_or_create_session_id()
    filters = {'session_id': session_id}
    if current_user.is_authenticated:
        filters = {'user_id': current_user.id}
    cart = Cart.query.filter_by(**filters).first()
    if not cart:
        cart = Cart(session_id=session_id, user_id=current_user.id if current_user.is_authenticated else None)
        db.session.add(cart)
        db.session.commit()
    return cart


@core_bp.app_context_processor
def inject_globals():
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order.asc()).all()
    cart_count = 0
    try:
        cart_count = sum(item.quantity for item in get_cart().items)
    except Exception:
        pass
    return {'nav_categories': categories, 'cart_count': cart_count}


@core_bp.route('/')
def home():
    featured_products = Product.query.filter_by(is_active=True, is_featured=True).limit(8).all()
    new_products = Product.query.filter_by(is_active=True, is_new=True).limit(8).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order.asc()).all()
    return render_template('shop/home.html', featured_products=featured_products, new_products=new_products, categories=categories)


@core_bp.route('/search')
def search():
    query = request.args.get('q', '')
    products = Product.query.filter(Product.is_active.is_(True), Product.name.ilike(f'%{query}%')).all()
    return render_template('shop/catalog.html', products=products, query=query, current_category=None)


@core_bp.route('/institucional/<page>')
def institutional(page):
    pages = {
        'sobre': 'Sobre a Caveira Atacado',
        'contato': 'Contato',
        'privacidade': 'Política de Privacidade',
        'termos': 'Termos de Uso',
        'trocas': 'Trocas e Devoluções'
    }
    if page not in pages:
        return redirect(url_for('core.home'))
    return render_template('shop/institutional.html', title=pages[page], page=page)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'danger')
            return redirect(url_for('auth.register'))
        user = User(full_name=request.form['full_name'], email=email, phone=request.form.get('phone'), cpf_cnpj=request.form.get('cpf_cnpj'))
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado com sucesso.', 'success')
        login_user(user)
        return redirect(url_for('user.dashboard'))
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'].strip().lower()).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            cart = Cart.query.filter_by(session_id=session.get('cart_session_id')).first()
            if cart and not cart.user_id:
                cart.user_id = user.id
                db.session.commit()
            flash('Login realizado com sucesso.', 'success')
            return redirect(request.args.get('next') or url_for('user.dashboard'))
        flash('Credenciais inválidas.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('core.home'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'].strip().lower()).first()
        if user:
            token = os.urandom(24).hex()
            reset = PasswordReset(user_id=user.id, token=token, expires_at=datetime.utcnow() + timedelta(hours=1))
            db.session.add(reset)
            db.session.commit()
            link = current_app.config['BASE_URL'] + url_for('auth.reset_password', token=token)
            send_email('Recuperação de senha', [user.email], f'Acesse o link para redefinir sua senha: {link}')
        flash('Se o e-mail existir, enviaremos um link de recuperação.', 'info')
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset = PasswordReset.query.filter_by(token=token, used=False).first_or_404()
    if reset.expires_at < datetime.utcnow():
        flash('Token expirado.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        user = User.query.get(reset.user_id)
        user.set_password(request.form['password'])
        reset.used = True
        db.session.commit()
        flash('Senha redefinida com sucesso.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', token=token)


@shop_bp.route('/catalog')
def catalog():
    category_slug = request.args.get('category')
    search_term = request.args.get('q')
    sort = request.args.get('sort', 'recent')
    products = Product.query.filter_by(is_active=True)
    current_category = None
    if category_slug:
        current_category = Category.query.filter_by(slug=category_slug).first()
        if current_category:
            products = products.filter_by(category_id=current_category.id)
    if search_term:
        products = products.filter(Product.name.ilike(f'%{search_term}%'))
    if sort == 'price_asc':
        products = products.order_by(Product.price.asc())
    elif sort == 'price_desc':
        products = products.order_by(Product.price.desc())
    else:
        products = products.order_by(Product.created_at.desc())
    return render_template('shop/catalog.html', products=products.all(), current_category=current_category, query=search_term)


@shop_bp.route('/product/<slug>', methods=['GET', 'POST'])
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related_products = Product.query.filter(Product.category_id == product.category_id, Product.id != product.id).limit(4).all()
    shipping_result = None
    if request.method == 'POST' and request.form.get('zipcode'):
        shipping_result = calculate_shipping(request.form['zipcode'])
    return render_template('shop/product_detail.html', product=product, related_products=related_products, shipping_result=shipping_result)


@cart_bp.route('/')
def view_cart():
    cart = get_cart()
    shipping = session.get('shipping_quote', {})
    return render_template('shop/cart.html', cart=cart, shipping=shipping)


@cart_bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = get_cart()
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    quantity = int(request.form.get('quantity', 1))
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)
        db.session.add(item)
    db.session.commit()
    flash('Produto adicionado ao carrinho.', 'success')
    return redirect(request.referrer or url_for('cart.view_cart'))


@cart_bp.route('/update/<int:item_id>', methods=['POST'])
def update_cart_item(item_id):
    item = CartItem.query.get_or_404(item_id)
    qty = max(1, int(request.form.get('quantity', 1)))
    item.quantity = qty
    db.session.commit()
    flash('Carrinho atualizado.', 'success')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
def remove_cart_item(item_id):
    item = CartItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item removido.', 'info')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/coupon', methods=['POST'])
def apply_coupon():
    cart = get_cart()
    code = request.form.get('coupon_code', '').strip().upper()
    coupon = Coupon.query.filter_by(code=code, is_active=True).first()
    if coupon:
        cart.coupon_id = coupon.id
        db.session.commit()
        flash('Cupom aplicado com sucesso.', 'success')
    else:
        flash('Cupom inválido.', 'danger')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/shipping', methods=['POST'])
def calculate_cart_shipping():
    result = calculate_shipping(request.form.get('zipcode'))
    if result.get('error'):
        flash(result['error'], 'danger')
    else:
        selected = result['shipping_options'][0]
        session['shipping_quote'] = selected | {'zipcode': result['zipcode'], 'city': result['city'], 'state': result['state']}
        flash('Frete calculado com sucesso.', 'success')
    return redirect(url_for('cart.view_cart'))


@checkout_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    cart = get_cart()
    if not cart.items:
        flash('Seu carrinho está vazio.', 'warning')
        return redirect(url_for('shop.catalog'))
    addresses = current_user.addresses
    shipping = session.get('shipping_quote')
    if request.method == 'POST':
        address = None
        if request.form.get('address_id'):
            address = UserAddress.query.get(int(request.form['address_id']))
        else:
            address = UserAddress(
                user_id=current_user.id,
                recipient_name=current_user.full_name,
                zipcode=request.form['zipcode'],
                street=request.form['street'],
                number=request.form['number'],
                complement=request.form.get('complement'),
                neighborhood=request.form.get('neighborhood'),
                city=request.form['city'],
                state=request.form['state'],
                reference=request.form.get('reference'),
                is_default=not addresses,
            )
            db.session.add(address)
            db.session.flush()

        shipping_cost = Decimal(str((shipping or {}).get('price', 0)))
        order = Order(
            user_id=current_user.id,
            subtotal=Decimal(str(cart.subtotal())),
            shipping_cost=shipping_cost,
            discount_amount=Decimal(str(cart.discount_amount())),
            total_amount=Decimal(str(cart.total(shipping_cost))),
            shipping_method=(shipping or {}).get('method', 'Entrega Padrão'),
            zipcode=address.zipcode,
            street=address.street,
            number=address.number,
            complement=address.complement,
            neighborhood=address.neighborhood,
            city=address.city,
            state=address.state,
        )
        db.session.add(order)
        db.session.flush()

        for item in cart.items:
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name,
                sku=item.product.sku,
                unit_price=item.product.final_price,
                quantity=item.quantity,
                total_price=Decimal(str(item.total_price()))
            ))
            item.product.stock -= item.quantity
        db.session.add(OrderStatusLog(order_id=order.id, status='aguardando_pagamento', note='Pedido criado no checkout.'))
        db.session.commit()

        mp = MercadoPagoService()
        preference = mp.create_preference(order, current_user.email)

        for item in cart.items[:]:
            db.session.delete(item)
        cart.coupon_id = None
        db.session.commit()
        session.pop('shipping_quote', None)

        return render_template('shop/checkout_success_redirect.html', order=order, preference=preference)

    return render_template('shop/checkout.html', cart=cart, addresses=addresses, shipping=shipping)


@checkout_bp.route('/confirmation/<int:order_id>')
@login_required
def confirmation(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('shop/order_confirmation.html', order=order)


@user_bp.route('/')
@login_required
def dashboard():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('user/dashboard.html', orders=orders)


@user_bp.route('/addresses', methods=['GET', 'POST'])
@login_required
def addresses():
    if request.method == 'POST':
        address = UserAddress(user_id=current_user.id, recipient_name=request.form['recipient_name'], zipcode=request.form['zipcode'], street=request.form['street'], number=request.form['number'], complement=request.form.get('complement'), neighborhood=request.form.get('neighborhood'), city=request.form['city'], state=request.form['state'], reference=request.form.get('reference'), is_default=not current_user.addresses)
        db.session.add(address)
        db.session.commit()
        flash('Endereço salvo com sucesso.', 'success')
        return redirect(url_for('user.addresses'))
    return render_template('user/addresses.html')


@user_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('user/order_detail.html', order=order)


@core_bp.route('/api/cep/<zipcode>')
def api_lookup_cep(zipcode):
    return jsonify(lookup_cep(zipcode))


@webhook_bp.route('/mercado-pago', methods=['POST'])
def mercado_pago():
    payload = request.get_json(silent=True) or {}
    data = payload.get('data', {})
    external_ref = None
    status = payload.get('action', 'pending')
    if 'external_reference' in payload:
        external_ref = payload['external_reference']
    elif 'order_id' in data:
        external_ref = data.get('order_id')

    if external_ref and str(external_ref).isdigit():
        order = Order.query.get(int(external_ref))
        if order:
            normalized = 'approved' if 'approved' in status else 'pending'
            if 'cancel' in status or 'rejected' in status:
                normalized = 'rejected'
            update_payment_from_webhook(order, data.get('id'), normalized, payload)
    return {'status': 'ok'}
