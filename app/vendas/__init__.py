from flask import Blueprint

bp = Blueprint('vendas', __name__)

from app.vendas import routes