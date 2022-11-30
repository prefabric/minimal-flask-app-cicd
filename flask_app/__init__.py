import os

from flask import Flask

from flask_app.extensions import (
    db,
    migrate,
)
from flask_app.blueprints import index


def create_app():
    app = Flask(__name__)

    env = os.environ.get('env')
    cfg = 'flask_app.config.ProdConfig'
    if env == 'LOCAL':
        cfg = 'flask_app.config.DevConfig'
    app.config.from_object(cfg)

    register_extensions(app)
    register_blueprints(app)

    return app


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app):
    app.register_blueprint(index.bp)


app = create_app()
