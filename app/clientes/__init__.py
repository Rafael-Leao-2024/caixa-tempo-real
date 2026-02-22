from flask import Blueprint

bp = Blueprint('clientes', __name__)

from app.clientes import routes