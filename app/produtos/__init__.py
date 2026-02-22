from flask import Blueprint

bp = Blueprint('produtos', __name__, url_prefix='/produtos')

from app.produtos import routes