import os
from functools import wraps
from urllib.parse import quote
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Product, Category, ProductImage, ProductVariation, ProductFlavor, Order, User, Coupon, HomeBanner, Brand, SiteSetting, get_site_setting
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


def _parse_bool(field_name):
    return bool(request.form.get(field_name))


def _normalize_whatsapp_number(value):
    return ''.join(char for char in (value or '') if char.isdigit())


def _parse_flavors(raw_value):
    unique_flavors = []
    seen = set()
    for chunk in (raw_value or '').replace('\r', '\n').split('\n'):
        for item in chunk.split(','):
            flavor = item.strip()
            if not flavor:
                continue
            normalized = flavor.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_flavors.append(flavor)
    return unique_flavors


def _sync_product_flavors(product, raw_value):
    flavors = _parse_flavors(raw_value)
    product.flavors.clear()
    for index, flavor in enumerate(flavors):
        product.flavors.append(ProductFlavor(name=flavor, display_order=index))


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


def _generate_unique_product_slug(base_name):
    base_slug = slugify(base_name)
    candidate = base_slug
    counter = 2
    while Product.query.filter_by(slug=candidate).first():
        candidate = f"{base_slug}-{counter}"
        counter += 1
    return candidate


def _generate_unique_product_sku(base_sku):
    base_sku = (base_sku or 'PRODUTO').strip()
    candidate = f"{base_sku}-COPY"
    counter = 2
    while Product.query.filter_by(sku=candidate).first():
        candidate = f"{base_sku}-COPY-{counter}"
        counter += 1
    return candidate


def _public_upload_path(filename):
    return f'/uploads/{filename}'


def _save_product_images(product, uploaded_files, replace_existing=False):
    valid_files = [file for file in uploaded_files if file and file.filename and allowed_file(file.filename)]
    if not valid_files:
        return False

    if replace_existing:
        for image in list(product.images):
            db.session.delete(image)
        db.session.flush()
    else:
        for image in product.images:
            image.is_primary = False

    for index, file in enumerate(valid_files):
        filename = unique_filename(file.filename)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        db.session.add(ProductImage(
            product_id=product.id,
            image_path=_public_upload_path(filename),
            alt_text=product.name,
            is_primary=(index == 0),
        ))

    return True


def _load_product_form_context(product=None):
    categories = Category.query.order_by(Category.name.asc()).all()
    brands = Brand.query.order_by(Brand.name.asc()).all()
    brands_by_category = {}
    for brand in brands:
        brands_by_category.setdefault(str(brand.category_id), []).append({
            'id': brand.id,
            'name': brand.name,
            'is_active': brand.is_active,
            'selected': bool(product and product.brand_id == brand.id),
        })
    return {
        'product': product,
        'categories': categories,
        'brands_by_category': brands_by_category,
    }


def _assign_product_form_data(product):
    category_id = int(request.form['category_id'])
    brand_id = request.form.get('brand_id', type=int)
    selected_brand = Brand.query.filter_by(id=brand_id, category_id=category_id).first() if brand_id else None

    product.category_id = category_id
    product.brand_id = selected_brand.id if selected_brand else None
    product.name = request.form['name']
    product.slug = slugify(request.form['name'])
    product.sku = request.form['sku']
    product.short_description = request.form.get('short_description')
    product.description = request.form.get('description')
    product.price = request.form['price']
    product.promotional_price = request.form.get('promotional_price') or None
    product.stock = request.form.get('stock', 0) or 0
    product.weight = request.form.get('weight', 0) or 0
    product.width = request.form.get('width', 0) or 0
    product.height = request.form.get('height', 0) or 0
    product.length = request.form.get('length', 0) or 0
    product.is_featured = _parse_bool('is_featured')
    product.is_new = _parse_bool('is_new')
    product.is_active = _parse_bool('is_active')
    product.redirect_to_whatsapp = _parse_bool('redirect_to_whatsapp')
    _sync_product_flavors(product, request.form.get('flavors'))


@admin_bp.route('/products/<int:product_id>/duplicate', methods=['POST'])
@admin_required
def duplicate_product(product_id):
    product = Product.query.get_or_404(product_id)
    duplicated_product = Product(
        category_id=product.category_id,
        brand_id=product.brand_id,
        name=f"{product.name} (Cópia)",
        slug=_generate_unique_product_slug(f"{product.name} copia"),
        sku=_generate_unique_product_sku(product.sku),
        short_description=product.short_description,
        description=product.description,
        price=product.price,
        promotional_price=product.promotional_price,
        stock=product.stock,
        weight=product.weight,
        width=product.width,
        height=product.height,
        length=product.length,
        is_featured=product.is_featured,
        is_new=product.is_new,
        is_active=product.is_active,
        redirect_to_whatsapp=product.redirect_to_whatsapp,
    )
    db.session.add(duplicated_product)
    db.session.flush()

    for image in product.images:
        db.session.add(ProductImage(
            product_id=duplicated_product.id,
            image_path=image.image_path,
            alt_text=image.alt_text,
            is_primary=image.is_primary,
        ))

    for variation in product.variations:
        db.session.add(ProductVariation(
            product_id=duplicated_product.id,
            name=variation.name,
            value=variation.value,
            stock=variation.stock,
        ))

    for flavor in product.flavors:
        db.session.add(ProductFlavor(
            product_id=duplicated_product.id,
            name=flavor.name,
            display_order=flavor.display_order,
        ))

    db.session.commit()
    flash('Produto duplicado com sucesso.', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Produto excluído com sucesso.', 'info')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def new_product():
    if request.method == 'POST':
        product = Product()
        _assign_product_form_data(product)
        db.session.add(product)
        db.session.flush()
        _save_product_images(product, request.files.getlist('images'))
        db.session.commit()
        flash('Produto cadastrado com sucesso.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', **_load_product_form_context())


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        _assign_product_form_data(product)
        if request.files.getlist('images'):
            _save_product_images(product, request.files.getlist('images'), replace_existing=True)
        db.session.commit()
        flash('Produto atualizado.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', **_load_product_form_context(product=product))


@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    editing_category = None
    editing_brand = None

    if request.method == 'POST':
        form_type = request.form.get('form_type', 'category')
        if form_type == 'brand':
            category_id = request.form.get('brand_category_id', type=int) or request.form.get('category_id', type=int)
            brand_id = request.form.get('brand_id', type=int)
            category = Category.query.get_or_404(category_id)
            if brand_id:
                brand = Brand.query.get_or_404(brand_id)
                brand.category_id = category.id
                brand.name = request.form['brand_name'] if request.form.get('brand_name') is not None else request.form['name']
                brand.slug = slugify(brand.name)
                brand.is_active = _parse_bool('brand_is_active') or _parse_bool('is_active')
                flash(f'Marca atualizada em {category.name}.', 'success')
            else:
                brand_name = request.form['brand_name'] if request.form.get('brand_name') is not None else request.form['name']
                brand = Brand(category_id=category.id, name=brand_name, slug=slugify(brand_name), is_active=_parse_bool('brand_is_active') or _parse_bool('is_active'))
                db.session.add(brand)
                flash(f'Marca criada em {category.name}.', 'success')
            db.session.commit()
            return redirect(url_for('admin.categories'))

        category_id = request.form.get('category_id')
        if category_id:
            editing_category = Category.query.get_or_404(category_id)
            editing_category.name = request.form['name']
            editing_category.slug = slugify(request.form['name'])
            editing_category.description = request.form.get('description')
            editing_category.display_order = request.form.get('display_order', 0)
            editing_category.is_active = _parse_bool('is_active')
            flash('Categoria atualizada.', 'success')
        else:
            category = Category(
                name=request.form['name'],
                slug=slugify(request.form['name']),
                description=request.form.get('description'),
                display_order=request.form.get('display_order', 0),
                is_active=_parse_bool('is_active')
            )
            db.session.add(category)
            flash('Categoria criada.', 'success')

        db.session.commit()
        return redirect(url_for('admin.categories'))

    edit_id = request.args.get('edit', type=int)
    if edit_id:
        editing_category = Category.query.get_or_404(edit_id)

    edit_brand_id = request.args.get('edit_brand', type=int)
    if edit_brand_id:
        editing_brand = Brand.query.get_or_404(edit_brand_id)

    categories = Category.query.order_by(Category.display_order.asc(), Category.name.asc()).all()
    return render_template('admin/categories.html', categories=categories, editing_category=editing_category, editing_brand=editing_brand)


@admin_bp.route('/brands/<int:brand_id>/delete', methods=['POST'])
@admin_required
def delete_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    if brand.products:
        flash('Não foi possível excluir a marca porque existem produtos vinculados a ela.', 'danger')
        return redirect(url_for('admin.categories'))
    db.session.delete(brand)
    db.session.commit()
    flash('Marca excluída com sucesso.', 'info')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    if category.products:
        flash('Não foi possível excluir a categoria porque existem produtos vinculados a ela.', 'danger')
        return redirect(url_for('admin.categories'))

    linked_banners = HomeBanner.query.filter_by(category_id=category.id).count()
    if linked_banners:
        flash('Não foi possível excluir a categoria porque existem banners vinculados a ela.', 'danger')
        return redirect(url_for('admin.categories'))

    try:
        db.session.delete(category)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Não foi possível excluir a categoria porque ela ainda possui vínculos no sistema.', 'danger')
        return redirect(url_for('admin.categories'))

    flash('Categoria excluída com sucesso.', 'info')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    setting = get_site_setting()
    if request.method == 'POST':
        setting.whatsapp_number = _normalize_whatsapp_number(request.form.get('whatsapp_number'))
        db.session.commit()
        flash('Configurações de WhatsApp atualizadas.', 'success')
        return redirect(url_for('admin.settings'))
    preview_message = quote('Olá! Tenho interesse em um produto da loja.')
    preview_link = f"https://wa.me/{setting.whatsapp_number}?text={preview_message}" if setting.whatsapp_number else None
    return render_template('admin/settings.html', setting=setting, preview_link=preview_link)


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
        uploaded_file = request.files.get('image')
        if uploaded_file and uploaded_file.filename and allowed_file(uploaded_file.filename):
            filename = unique_filename(uploaded_file.filename)
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(save_path)
            image_path = _public_upload_path(filename)

        banner = HomeBanner(
            title=request.form['title'],
            subtitle=request.form.get('subtitle'),
            button_text=request.form.get('button_text') or 'Ver categoria',
            custom_url=request.form.get('custom_url'),
            image_path=image_path,
            display_order=request.form.get('display_order', 0) or 0,
            is_active=bool(request.form.get('is_active')),
            category_id=request.form.get('category_id') or None,
        )
        db.session.add(banner)
        db.session.commit()
        flash('Banner salvo com sucesso.', 'success')
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
            banner.image_path = _public_upload_path(filename)
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
