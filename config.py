import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or "chaihongjing"
    SSL_REDIRECT = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    FLASKY_PER_PAGE = 10
    SQLALCHEMY_POOL_SIZE=5


    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:11111111@127.0.0.1:3306/management2.0"




class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:11111111@172.18.0.3:3306/management2.0"

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig,
    'production': ProductionConfig
}