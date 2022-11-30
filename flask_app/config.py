import os


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_USER = os.environ.get('FLASK_APP_DB_USER')
    DB_PASS = os.environ.get('FLASK_APP_DB_PASS')
    DB_URL = os.environ.get('FLASK_APP_DB_URL')
    DB_NAME = os.environ.get('FLASK_APP_DB_NAME')
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}/{}'.format(
        DB_USER,
        DB_PASS,
        DB_URL,
        DB_NAME,
    )


class ProdConfig(Config):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')


class DevConfig(Config):
    TESTING = True
    DEBUG = True
    SECRET_KEY = 'dev'
