import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Product, Category, ProductImage, Order, User, Coupon, HomeBanner
from ..utils.helpers import slugify, allowed_file, unique_filename

admin_bp = Blueprint('admin', __name__)


def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acesso restrito ao painel administrativo.', 'danger')
            return redirect(url_for('core.home'))
        return func(*args, **kwargs)
    return wrapper


@admin_bp.route('/')
@admin_required
def dashboard():
    orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    total_sales = sum(float(order.total_amount) for order in Order.query.filter(Order.payment_status.in_(['approved', 'paid'])).all())
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(is_admin=False).count()
    avg_ticket = total_sales / total_orders if total_orders else 0
    top_products = Product.query.order_by(Product.stock.asc()).limit(5).all()
    return render_template('admin/dashboard.html', orders=orders, total_sales=total_sales, total_orders=total_orders, total_customers=total_customers, avg_ticket=avg_ticket, top_products=top_products)


@admin_bp.route('/products')
@admin_required
def products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)


@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def new_product():
    categories = Category.query.order_by(Category.name.asc()).all()
    if request.method == 'POST':
        product = Product(
            category_id=request.form['category_id'],
            name=request.form['name'],
            slug=slugify(request.form['name']),
            sku=request.form['sku'],
            short_description=request.form.get('short_description'),
            description=request.form.get('description'),
            price=request.form['price'],
            promotional_price=request.form.get('promotional_price') or None,
            stock=request.form.get('stock', 0),
            weight=request.form.get('weight', 0),
            width=request.form.get('width', 0),
            height=request.form.get('height', 0),
            length=request.form.get('length', 0),
            is_featured=bool(request.form.get('is_featured')),
            is_new=bool(request.form.get('is_new')),
            is_active=bool(request.form.get('is_active')),
        )
        db.session.add(product)
        db.session.flush()

        for file in request.files.getlist('images'):
            if file and allowed_file(file.filename):
                filename = unique_filename(file.filename)
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                db.session.add(ProductImage(product_id=product.id, image_path='/' + save_path.replace('app/', ''), is_primary=False))
        db.session.commit()
        flash('Produto cadastrado com sucesso.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=None, categories=categories)


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name.asc()).all()
    if request.method == 'POST':
        product.category_id = request.form['category_id']
        product.name = request.form['name']
        product.slug = slugify(request.form['name'])
        product.sku = request.form['sku']
        product.short_description = request.form.get('short_description')
        product.description = request.form.get('description')
        product.price = request.form['price']
        product.promotional_price = request.form.get('promotional_price') or None
        product.stock = request.form.get('stock', 0)
        product.is_featured = bool(request.form.get('is_featured'))
        product.is_new = bool(request.form.get('is_new'))
        product.is_active = bool(request.form.get('is_active'))
        db.session.commit()
        flash('Produto atualizado.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=product, categories=categories)


@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    if request.method == 'POST':
        category = Category(name=request.form['name'], slug=slugify(request.form['name']), description=request.form.get('description'), display_order=request.form.get('display_order', 0), is_active=bool(request.form.get('is_active')))
        db.session.add(category)
        db.session.commit()
        flash('Categoria criada.', 'success')
        return redirect(url_for('admin.categories'))
    categories = Category.query.order_by(Category.display_order.asc()).all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/orders')
@admin_required
def orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form['status']
    db.session.commit()
    flash('Status atualizado.', 'success')
    return redirect(url_for('admin.orders'))


@admin_bp.route('/customers')
@admin_required
def customers():
    customers = User.query.filter_by(is_admin=False).all()
    return render_template('admin/customers.html', customers=customers)


@admin_bp.route('/coupons', methods=['GET', 'POST'])
@admin_required
def coupons():
    if request.method == 'POST':
        coupon = Coupon(code=request.form['code'].upper(), discount_type=request.form['discount_type'], discount_value=request.form['discount_value'], is_active=bool(request.form.get('is_active')))
        db.session.add(coupon)
        db.session.commit()
        flash('Cupom criado.', 'success')
        return redirect(url_for('admin.coupons'))
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons)


@admin_bp.route('/banners', methods=['GET', 'POST'])
@admin_required
def banners():
    categories = Category.query.order_by(Category.name.asc()).all()
    if request.method == 'POST':
        image_path = request.form.get('existing_image_path') or ''
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = unique_filename(file.filename)
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            image_path = '/' + save_path.replace('app/', '')

        banner = HomeBanner(
            title=request.form['title'],
            subtitle=request.form.get('subtitle'),
            button_text=request.form.get('button_text') or 'Ver categoria',
            custom_url=request.form.get('custom_url') or None,
            image_path=image_path or None,
            display_order=request.form.get('display_order', 0),
            is_active=bool(request.form.get('is_active')),
            category_id=request.form.get('category_id') or None,
        )
        db.session.add(banner)
        db.session.commit()
        flash('Banner criado com sucesso.', 'success')
        return redirect(url_for('admin.banners'))

    banners = HomeBanner.query.order_by(HomeBanner.display_order.asc(), HomeBanner.created_at.desc()).all()
    return render_template('admin/banners.html', banners=banners, categories=categories)


@admin_bp.route('/banners/<int:banner_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_banner(banner_id):
    banner = HomeBanner.query.get_or_404(banner_id)
    categories = Category.query.order_by(Category.name.asc()).all()
    if request.method == 'POST':
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = unique_filename(file.filename)
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            banner.image_path = '/' + save_path.replace('app/', '')
        else:
            banner.image_path = request.form.get('existing_image_path') or banner.image_path

        banner.title = request.form['title']
        banner.subtitle = request.form.get('subtitle')
        banner.button_text = request.form.get('button_text') or 'Ver categoria'
        banner.custom_url = request.form.get('custom_url') or None
        banner.display_order = request.form.get('display_order', 0)
        banner.is_active = bool(request.form.get('is_active'))
        banner.category_id = request.form.get('category_id') or None
        db.session.commit()
        flash('Banner atualizado.', 'success')
        return redirect(url_for('admin.banners'))

    return render_template('admin/banner_form.html', banner=banner, categories=categories)


@admin_bp.route('/banners/<int:banner_id>/delete', methods=['POST'])
@admin_required
def delete_banner(banner_id):
    banner = HomeBanner.query.get_or_404(banner_id)
    db.session.delete(banner)
    db.session.commit()
    flash('Banner removido.', 'info')
    return redirect(url_for('admin.banners'))
