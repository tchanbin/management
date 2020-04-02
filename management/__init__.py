#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown
from config import config
import flask_excel as excel


bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()

login_manager = LoginManager()
login_manager.login_view = 'home.login'
login_manager.login_message = u"用户未登录，请先登录。"


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    excel.init_excel(app)

    if app.config['SSL_REDIRECT']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    from .home import home as blueprint_home
    app.register_blueprint(blueprint_home)

    from .admin import admin as blueprint_admin
    app.register_blueprint(blueprint_admin, url_prefix="/admin")

    # from .main import main as main_blueprint
    # app.register_blueprint(main_blueprint)
    #
    # from .auth import auth as auth_blueprint
    # app.register_blueprint(auth_blueprint, url_prefix='/auth')
    #
    # from .api import api as api_blueprint
    # app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app
