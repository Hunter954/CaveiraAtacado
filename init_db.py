from sqlalchemy import inspect
from app import create_app
from app.extensions import db
from app.models import seed_data

app = create_app()


def ensure_database_ready() -> None:
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        expected_tables = set(db.metadata.tables.keys())
        missing_tables = expected_tables - existing_tables

        if missing_tables:
            db.create_all()

        if app.config.get('AUTO_SEED_DATA', True):
            seed_data()


if __name__ == '__main__':
    ensure_database_ready()
    print('Database bootstrap finished.')
