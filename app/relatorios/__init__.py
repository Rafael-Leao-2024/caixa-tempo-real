from flask import Blueprint

bp = Blueprint('relatorios', __name__)

from app.relatorios import routes