from flask import Blueprint

bp = Blueprint('relatorios', __name__)

from caixa.relatorios import routes