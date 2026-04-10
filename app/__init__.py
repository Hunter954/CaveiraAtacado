import logging
import os
from flask import Flask
from sqlalchemy import inspect
from .config import Config
from .extensions import db, migrate, login_manager, mail
from .routes import core_bp, auth_bp, shop_bp, cart_bp, checkout_bp, user_bp, webhook_bp
from .admin.routes import admin_bp
from .models import User, seed_data

logger = logging.getLogger(__name__)


def bootstrap_database(app):
    auto_create_db = app.config.get('AUTO_CREATE_DB', True)
    auto_seed = app.config.get('AUTO_SEED_DATA', True)

    if not auto_create_db:
        logger.info('AUTO_CREATE_DB=false; pulando inicializacao do banco.')
        return

    with app.app_context():
        # Garante que todos os models estejam registrados no metadata antes do create_all.
        from . import models  # noqa: F401

        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        expected_tables = set(db.metadata.tables.keys())
        missing_tables = expected_tables.difference(existing_tables)

        if missing_tables:
            logger.info('Criando tabelas ausentes: %s', ', '.join(sorted(missing_tables)))
            db.create_all()
        else:
            logger.info('Todas as tabelas ja existem no banco.')

        if auto_seed:
            try:
                seed_data()
                logger.info('Seed inicial verificado/aplicado com sucesso.')
            except Exception:
                logger.exception('Falha ao aplicar seed inicial.')
                db.session.rollback()
                raise


def brl_currency(value):
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0.0
    formatted = f"{number:,.2f}"
    return formatted.replace(',', 'X').replace('.', ',').replace('X', '.')


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    app.jinja_env.filters['brl_currency'] = brl_currency

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(shop_bp, url_prefix='/shop')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(checkout_bp, url_prefix='/checkout')
    app.register_blueprint(user_bp, url_prefix='/account')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(webhook_bp, url_prefix='/webhooks')

    @app.cli.command('seed')
    def seed_command():
        seed_data()
        print('Dados iniciais criados com sucesso.')

    bootstrap_database(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
