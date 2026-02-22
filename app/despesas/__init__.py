from flask import Blueprint

bp = Blueprint('despesas', __name__, url_prefix='/despesas')

from app.despesas import routes