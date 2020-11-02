import logging
import os
import hashlib


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', default=hashlib.sha512(os.urandom(10)).hexdigest())

    # sqlalchemy
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_POOL_PRE_PING = True
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 280
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OAuth
    OAUTH_CONSUMER_KEY = ''
    OAUTH_CONSUMER_SECRET = ''

    # Flask caching
    CACHE_REDIS_HOST = 'redis'

    # Kube
    IMAGE_PULL_POLICY = "Always"

    def __init__(self):
        self.DEBUG = os.environ.get('DEBUG', default='0') == '1'

        # Sqlalchemy
        self.SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI',
            default='mysql+pymysql://anubis:anubis@{}/anubis'.format(
                os.environ.get('DB_HOST', 'db')))

        # Redis
        self.CACHE_REDIS_HOST = os.environ.get('CACHE_REDIS_HOST', default='redis')

        # Kube
        self.IMAGE_PULL_POLICY = os.environ.get('IMAGE_PULL_POLICY', default='Always')

        logging.info('Starting with DATABASE_URI: {}'.format(
            self.SQLALCHEMY_DATABASE_URI))
        logging.info('Starting with SECRET_KEY: {}'.format(self.SECRET_KEY))
        logging.info('Starting with DEBUG: {}'.format(self.DEBUG))


config = Config()
