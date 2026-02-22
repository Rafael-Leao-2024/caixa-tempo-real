from flask import Blueprint

bp = Blueprint('clientes', __name__)

from caixa.clientes import routes