import logging

from flask import Flask
from anubis.utils.logger import logger

logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


def init_services(app):
    """
    Initialize app with redis cache, mariadb database, and ELK services

    :param app: Flask app
    :return:
    """
    from anubis.models import db, Config
    from anubis.utils.cache import cache
    from anubis.config import config

    # Init services
    db.init_app(app)
    cache.init_app(app)

    # Initialize the DB
    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return 'Hello there...!'


def create_app():
    """
    Create the main Anubis API Flask app instance

    This app will have the basic services (db and cache),
    with the public and private blueprints.

    :return: Flask app
    """
    from anubis.config import config
    from anubis.routes.public import public

    # Create app
    app = Flask(__name__)
    app.config.from_object(config)

    init_services(app)

    # register blueprints
    app.register_blueprint(public)

    return app


def create_pipeline_app():
    """
    Create the Submission Pipeline API Flask app instance

    This app will have the basic services (db and cache),
    with the pipeline blueprint.

    :return: Flask app
    """
    from anubis.config import config
    from anubis.routes.pipeline import pipeline

    # Create app
    app = Flask(__name__)
    app.config.from_object(config)

    init_services(app)

    # register blueprints
    app.register_blueprint(pipeline)

    return app
