from flask import Blueprint

bp = Blueprint('auth', __name__)

from caixa.auth import routes