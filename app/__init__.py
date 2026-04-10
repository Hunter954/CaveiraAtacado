import os
from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, mail
from .routes import core_bp, auth_bp, shop_bp, cart_bp, checkout_bp, user_bp, webhook_bp
from .admin.routes import admin_bp
from .models import User, seed_data


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

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

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
