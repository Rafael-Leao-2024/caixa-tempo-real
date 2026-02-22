from flask import Blueprint

bp = Blueprint('main', __name__)

from caixa.main import routes