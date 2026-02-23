from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from caixa import db
from caixa.relatorios import bp
from caixa.models import Venda, Pagamento, Cliente, Caixa, FluxoCaixa
from caixa.decoradores import owner_required, caixa_required
from datetime import datetime, date, timedelta

@bp.route('/diario')
@login_required
@caixa_required
def relatorio_diario():
    data = request.args.get('data', date.today().strftime('%Y-%m-%d'))
    data_obj = datetime.strptime(data, '%Y-%m-%d').date()
    
    # Filtrar por caixa se não for owner
    query = Venda.query
    if not current_user.is_owner and current_user.caixa_id:
        query = query.filter_by(caixa_id=current_user.caixa_id)
    
    # Vendas do dia
    vendas = query.filter(
        db.func.date(Venda.data_venda) == data_obj
    ).all()
    
    # Pagamentos do dia
    pagamentos_query = Pagamento.query
    if not current_user.is_owner and current_user.caixa_id:
        pagamentos_query = pagamentos_query.join(Venda).filter(Venda.caixa_id == current_user.caixa_id)
    
    pagamentos = pagamentos_query.filter(
        db.func.date(Pagamento.data_pagamento) == data_obj
    ).all()
    
    # Cálculos
    total_vendas_vista = sum(v.valor_total for v in vendas if v.tipo_pagamento == 'vista')
    total_vendas_prazo = sum(v.valor_total for v in vendas if v.tipo_pagamento == 'prazo')
    total_recebimentos = sum(p.valor for p in pagamentos)
    
    # Recebimentos de vendas antigas
    recebimentos_prazo = sum(p.valor for p in pagamentos if p.venda.tipo_pagamento == 'prazo')
    
    context = {
        'data': data_obj,
        'vendas': vendas,
        'pagamentos': pagamentos,
        'total_vendas_vista': total_vendas_vista,
        'total_vendas_prazo': total_vendas_prazo,
        'total_vendas': total_vendas_vista + total_vendas_prazo,
        'total_recebimentos': total_recebimentos,
        'recebimentos_prazo': recebimentos_prazo,
        'saldo_dia': total_vendas_vista + recebimentos_prazo
    }
    
    return render_template('relatorios/diario.html', **context)

# @bp.route('/geral')
# @login_required
# @owner_required
# def relatorio_geral():
#     # Período
#     data_inicio = request.args.get('data_inicio', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
#     data_fim = request.args.get('data_fim', date.today().strftime('%Y-%m-%d'))
    
#     inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
#     fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
#     # Vendas por período
#     vendas = Venda.query.filter(
#         db.func.date(Venda.data_venda) >= inicio,
#         db.func.date(Venda.data_venda) <= fim
#     ).all()
    
#     # Totais por caixa
#     caixas = Caixa.query.all()
#     dados_caixas = []
    
#     for caixa in caixas:
#         vendas_caixa = [v for v in vendas if v.caixa_id == caixa.id]
#         total_vendas = sum(v.valor_total for v in vendas_caixa)
#         total_recebido = sum(v.valor_pago for v in vendas_caixa)
        
#         dados_caixas.append({
#             'caixa': caixa,
#             'total_vendas': total_vendas,
#             'total_recebido': total_recebido,
#             'quantidade_vendas': len(vendas_caixa)
#         })
    
#     # Clientes com débito
#     clientes_devedores = Cliente.query.filter(Cliente.saldo_devedor > 0).all()
#     total_a_receber = sum(c.saldo_devedor for c in clientes_devedores)
    
#     context = {
#         'data_inicio': inicio,
#         'data_fim': fim,
#         'vendas': vendas,
#         'dados_caixas': dados_caixas,
#         'clientes_devedores': clientes_devedores,
#         'total_a_receber': total_a_receber,
#         'total_vendas_periodo': sum(v.valor_total for v in vendas),
#         'total_recebido_periodo': sum(v.valor_pago for v in vendas)
#     }
    
#     return render_template('relatorios/geral.html', **context)

@bp.route('/geral')
@login_required
@owner_required
def relatorio_geral():
    # Período
    data_inicio = request.args.get('data_inicio', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    data_fim = request.args.get('data_fim', date.today().strftime('%Y-%m-%d'))
    
    inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    # Vendas por período
    vendas = Venda.query.filter(
        db.func.date(Venda.data_venda) >= inicio,
        db.func.date(Venda.data_venda) <= fim
    ).all()
    
    # ===== NOVO: Buscar fluxos de caixa do período =====
    fluxos_periodo = FluxoCaixa.query.filter(
        FluxoCaixa.data >= inicio,
        FluxoCaixa.data <= fim
    ).order_by(FluxoCaixa.data).all()
    
    # Totais por caixa
    caixas = Caixa.query.all()
    dados_caixas = []
    
    for caixa in caixas:
        vendas_caixa = [v for v in vendas if v.caixa_id == caixa.id]
        total_vendas = sum(v.valor_total for v in vendas_caixa)
        total_recebido = sum(v.valor_pago for v in vendas_caixa)
        total_vistas = sum(v.valor_total for v in vendas_caixa if v.tipo_pagamento == 'vista')
        total_prazos = sum(v.valor_total for v in vendas_caixa if v.tipo_pagamento == 'prazo')
        
        # Calcular saldo do período para este caixa
        fluxos_caixa = [f for f in fluxos_periodo if f.caixa_id == caixa.id]
        saldo_periodo = fluxos_caixa[-1].saldo_final - fluxos_caixa[0].saldo_inicial if fluxos_caixa else 0
        
        dados_caixas.append({
            'caixa': caixa,
            'total_vendas': total_vendas,
            'total_recebido': total_recebido,
            'quantidade_vendas': len(vendas_caixa),
            'total_vistas': total_vistas,
            'total_prazos': total_prazos,
            'saldo_periodo': saldo_periodo
        })
    
    # Clientes com débito
    clientes_devedores = Cliente.query.filter(Cliente.saldo_devedor > 0).all()
    total_a_receber = sum(c.saldo_devedor for c in clientes_devedores)
    
    context = {
        'data_inicio': inicio,
        'data_fim': fim,
        'vendas': vendas,
        'fluxos_periodo': fluxos_periodo,  # NOVO
        'dados_caixas': dados_caixas,
        'clientes_devedores': clientes_devedores,
        'total_a_receber': total_a_receber,
        F'total_vendas_periodo': sum(v.valor_total for v in vendas),
        'total_recebido_periodo': sum(v.valor_pago for v in vendas)
    }
    print(fluxos_periodo)
    return render_template('relatorios/geral.html', **context)


@bp.route('/fluxo-tempo-real')
@login_required
def fluxo_tempo_real():
    """API para atualização em tempo real do dashboard"""
    hoje = date.today()
    
    # Vendas do dia
    vendas_hoje = Venda.query.filter(
        db.func.date(Venda.data_venda) == hoje
    ).all()
    
    # Se for operador de caixa, filtrar por seu caixa
    if not current_user.is_owner and current_user.caixa_id:
        vendas_hoje = [v for v in vendas_hoje if v.caixa_id == current_user.caixa_id]
    
    dados = {
        'total_vendas': sum(v.valor_total for v in vendas_hoje),
        'total_recebido': sum(v.valor_pago for v in vendas_hoje),
        'quantidade_vendas': len(vendas_hoje),
        'vendas_prazo': len([v for v in vendas_hoje if v.tipo_pagamento == 'prazo']),
        'vendas_vista': len([v for v in vendas_hoje if v.tipo_pagamento == 'vista'])
    }
    
    return jsonify(dados)