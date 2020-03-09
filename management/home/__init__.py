from flask import Blueprint
from management import models
from management.models import Permission

home = Blueprint('home', __name__)

from . import forms, views, errors


@home.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
