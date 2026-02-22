from flask import Blueprint

bp = Blueprint('produtos', __name__, url_prefix='/produtos')

from caixa.produtos import routes