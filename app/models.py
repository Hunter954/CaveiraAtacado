from datetime import datetime
from decimal import Decimal
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(UserMixin, TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30))
    cpf_cnpj = db.Column(db.String(30))
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active_user = db.Column(db.Boolean, default=True)

    addresses = db.relationship('UserAddress', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserAddress(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_name = db.Column(db.String(150), nullable=False)
    zipcode = db.Column(db.String(20), nullable=False)
    street = db.Column(db.String(255), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    complement = db.Column(db.String(120))
    neighborhood = db.Column(db.String(120))
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(10), nullable=False)
    reference = db.Column(db.String(255))
    is_default = db.Column(db.Boolean, default=False)


class Category(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)

    products = db.relationship('Product', backref='category', lazy=True)
    brands = db.relationship('Brand', backref='category', lazy=True, cascade='all, delete-orphan', order_by='Brand.name.asc()')


class Brand(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(150), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    __table_args__ = (db.UniqueConstraint('category_id', 'slug', name='uq_brand_category_slug'),)

    products = db.relationship('Product', backref='brand', lazy=True)


class SiteSetting(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    whatsapp_number = db.Column(db.String(30))


class HomeBanner(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    subtitle = db.Column(db.Text)
    button_text = db.Column(db.String(80), default='Ver categoria')
    custom_url = db.Column(db.String(255))
    image_path = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    category = db.relationship('Category')


class Product(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    name = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False)
    sku = db.Column(db.String(60), unique=True, nullable=False)
    short_description = db.Column(db.String(255))
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    promotional_price = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer, default=0)
    weight = db.Column(db.Float, default=0.0)
    width = db.Column(db.Float, default=0.0)
    height = db.Column(db.Float, default=0.0)
    length = db.Column(db.Float, default=0.0)
    is_featured = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    redirect_to_whatsapp = db.Column(db.Boolean, default=False)

    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    variations = db.relationship('ProductVariation', backref='product', lazy=True, cascade='all, delete-orphan')
    flavors = db.relationship('ProductFlavor', backref='product', lazy=True, cascade='all, delete-orphan', order_by='ProductFlavor.display_order.asc(), ProductFlavor.name.asc()')

    @property
    def final_price(self):
        return self.promotional_price or self.price

    @property
    def requires_whatsapp_redirect(self):
        return bool(self.redirect_to_whatsapp)


class ProductImage(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(180))
    is_primary = db.Column(db.Boolean, default=False)


class ProductVariation(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    value = db.Column(db.String(80), nullable=False)
    stock = db.Column(db.Integer, default=0)


class ProductFlavor(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    display_order = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint('product_id', 'name', name='uq_product_flavor_name'),)


class Coupon(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), nullable=False, default='percent')
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    max_uses = db.Column(db.Integer)
    used_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime)

    def apply_discount(self, subtotal):
        subtotal = Decimal(subtotal)
        if self.discount_type == 'fixed':
            return min(subtotal, Decimal(self.discount_value))
        return subtotal * (Decimal(self.discount_value) / Decimal('100'))


class Cart(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(120), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupon.id'))

    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')
    coupon = db.relationship('Coupon')

    def subtotal(self):
        return sum(item.total_price() for item in self.items)

    def discount_amount(self):
        if self.coupon:
            return float(self.coupon.apply_discount(self.subtotal()))
        return 0.0

    def total(self, shipping=0):
        return float(self.subtotal()) - self.discount_amount() + float(shipping)


class CartItem(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship('Product')

    def total_price(self):
        return float(self.product.final_price) * self.quantity


class Order(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='aguardando_pagamento')
    payment_status = db.Column(db.String(50), default='pending')
    shipping_status = db.Column(db.String(50), default='pending')
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_cost = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_method = db.Column(db.String(80))
    zipcode = db.Column(db.String(20))
    street = db.Column(db.String(255))
    number = db.Column(db.String(20))
    complement = db.Column(db.String(120))
    neighborhood = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(10))
    tracking_code = db.Column(db.String(80))

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='order', lazy=True, cascade='all, delete-orphan')
    status_logs = db.relationship('OrderStatusLog', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderItem(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    product_name = db.Column(db.String(180), nullable=False)
    sku = db.Column(db.String(60))
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    product = db.relationship('Product')


class Payment(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    provider = db.Column(db.String(50), default='mercado_pago')
    payment_type = db.Column(db.String(50), nullable=False)
    external_id = db.Column(db.String(120))
    preference_id = db.Column(db.String(120))
    status = db.Column(db.String(50), default='pending')
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    raw_response = db.Column(db.Text)


class ShippingQuote(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zipcode = db.Column(db.String(20), nullable=False)
    method = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_days = db.Column(db.Integer, nullable=False)


class PasswordReset(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(120), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)


class OrderStatusLog(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    note = db.Column(db.String(255))


def get_site_setting():
    setting = SiteSetting.query.order_by(SiteSetting.id.asc()).first()
    if not setting:
        setting = SiteSetting(whatsapp_number='')
        db.session.add(setting)
        db.session.flush()
    return setting


def seed_data():
    categories = Category.query.order_by(Category.display_order.asc()).all()

    if not categories:
        categories = [
            Category(name='Eletrônicos', slug='eletronicos', display_order=1),
            Category(name='Moda', slug='moda', display_order=2),
            Category(name='Casa', slug='casa', display_order=3),
            Category(name='Games', slug='games', display_order=4),
        ]
        db.session.add_all(categories)
        db.session.flush()

    default_brands = {
        'eletronicos': ['Caveira Tech', 'Phantom'],
        'moda': ['Nike', 'Adidas'],
        'casa': ['Raven Home'],
        'games': ['Skull One'],
    }
    for category in categories:
        if not category.brands:
            for brand_name in default_brands.get(category.slug, [category.name]):
                db.session.add(Brand(category_id=category.id, name=brand_name, slug=brand_name.lower().replace(' ', '-'), is_active=True))
    db.session.flush()

    if not Product.query.first():
        brand_map = {}
        for brand in Brand.query.all():
            brand_map.setdefault(brand.category.slug, brand)

        products = [
            Product(category_id=categories[0].id, brand_id=brand_map.get('eletronicos').id if brand_map.get('eletronicos') else None, name='Headset Caveira Pro', slug='headset-caveira-pro', sku='CAV-HEAD-001', short_description='Headset gamer premium.', description='Headset gamer com acabamento premium em vermelho e preto.', price=399.90, promotional_price=329.90, stock=15, is_featured=True, is_new=True),
            Product(category_id=categories[0].id, brand_id=brand_map.get('eletronicos').id if brand_map.get('eletronicos') else None, name='Smartphone Phantom X', slug='smartphone-phantom-x', sku='CAV-PHONE-001', short_description='Tela AMOLED e alta performance.', description='Smartphone com foco em performance e design premium.', price=2899.90, promotional_price=2599.90, stock=7, is_featured=True),
            Product(category_id=categories[3].id, brand_id=brand_map.get('games').id if brand_map.get('games') else None, name='Controle Skull One', slug='controle-skull-one', sku='CAV-GAME-001', short_description='Controle ergonômico para games.', description='Controle com pegada confortável e excelente resposta.', price=249.90, promotional_price=199.90, stock=30, is_featured=True),
            Product(category_id=categories[2].id, brand_id=brand_map.get('casa').id if brand_map.get('casa') else None, name='Poltrona Raven', slug='poltrona-raven', sku='CAV-HOME-001', short_description='Conforto para seu setup.', description='Poltrona moderna para casa ou escritório.', price=799.90, stock=9, is_new=True),
        ]
        db.session.add_all(products)
        db.session.flush()

        for product in products:
            db.session.add(ProductImage(product_id=product.id, image_path='https://placehold.co/600x600/f8f9fa/d90429?text=Caveira+Atacado', is_primary=True))

    if not HomeBanner.query.first() and categories:
        db.session.add_all([
            HomeBanner(
                title='Linha premium em destaque',
                subtitle='Destaque categorias e promoções em banners rotativos gerenciados pelo painel administrativo.',
                button_text='Ver categoria',
                category_id=categories[0].id,
                image_path='https://placehold.co/1200x520/f8f9fa/d90429?text=Caveira+Atacado',
                display_order=1,
                is_active=True,
            ),
            HomeBanner(
                title='Ofertas que o admin controla',
                subtitle='Escolha a categoria, imagem e ordem de exibição de cada banner direto no admin.',
                button_text='Comprar agora',
                category_id=categories[-1].id,
                image_path='https://placehold.co/1200x520/f8f9fa/111111?text=Banner+Caveira',
                display_order=2,
                is_active=True,
            ),
        ])

    if not User.query.filter_by(email='admin@caveiraatacado.com').first():
        admin = User(full_name='Administrador Caveira', email='admin@caveiraatacado.com', phone='11999999999', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)

    if not Coupon.query.filter_by(code='CAVEIRA10').first():
        coupon = Coupon(code='CAVEIRA10', discount_type='percent', discount_value=10)
        db.session.add(coupon)

    get_site_setting()
    db.session.commit()
