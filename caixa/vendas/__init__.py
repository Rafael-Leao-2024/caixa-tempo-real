from flask import Blueprint

bp = Blueprint('vendas', __name__)

from caixa.vendas import routes