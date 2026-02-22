from flask import render_template
from flask_login import login_required, current_user
from app.main import bp
from app.models import Venda, Cliente, Caixa
from app.extensoes import db
from datetime import datetime, date

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # Dados para o dashboard
    hoje = date.today()
    
    # Vendas do dia
    vendas_hoje = Venda.query.filter(
        db.func.date(Venda.data_venda) == hoje
    ).all()
    
    total_vendas_hoje = sum(v.valor_total for v in vendas_hoje)
    total_recebido_hoje = sum(v.valor_pago for v in vendas_hoje)
    
    # Clientes com débito
    clientes_devedores = Cliente.query.filter(Cliente.saldo_devedor > 0).all()
    
    # Status do caixa atual (se for operador de caixa)
    caixa_atual = None
    if current_user.caixa_id:
        caixa_atual = Caixa.query.get(current_user.caixa_id)
    
    context = {
        'vendas_hoje': vendas_hoje,
        'total_vendas_hoje': total_vendas_hoje,
        'total_recebido_hoje': total_recebido_hoje,
        'clientes_devedores': clientes_devedores,
        'caixa_atual': caixa_atual
    }
    
    return render_template('index.html', **context)