from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from caixa import db
from caixa.clientes import bp
from caixa.clientes.forms import ClienteForm
from caixa.models import Cliente, Venda
from caixa.decoradores import caixa_required

@bp.route('/')
@login_required
@caixa_required
def lista_clientes():
    page = request.args.get('page', 1, type=int)
    clientes = Cliente.query.order_by(Cliente.nome).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('clientes/lista.html', clientes=clientes)

@bp.route('/novo', methods=['GET', 'POST'])
@login_required
@caixa_required
def novo_cliente():
    form = ClienteForm()
    if form.validate_on_submit():
        cliente = Cliente(
            nome=form.nome.data,
            telefone=form.telefone.data,
            email=form.email.data,
            tipo_pagamento=form.tipo_pagamento.data,
            limite_credito=form.limite_credito.data,
            observacoes=form.observacoes.data
        )
        db.session.add(cliente)
        db.session.commit()
        flash(f'Cliente {cliente.nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('clientes.lista_clientes'))
    
    return render_template('clientes/novo.html', form=form)

@bp.route('/<int:id>')
@login_required
@caixa_required
def detalhe_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    vendas = Venda.query.filter_by(cliente_id=id).order_by(Venda.data_venda.desc()).all()
    
    # Calcular totais
    total_compras = sum(v.valor_total for v in vendas)
    total_pago = sum(v.valor_pago for v in vendas)
    
    context = {
        'cliente': cliente,
        'vendas': vendas,
        'total_compras': total_compras,
        'total_pago': total_pago
    }
    
    return render_template('clientes/detalhe.html', **context)

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@caixa_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    form = ClienteForm(obj=cliente)
    
    if form.validate_on_submit():
        cliente.nome = form.nome.data
        cliente.telefone = form.telefone.data
        cliente.email = form.email.data
        cliente.tipo_pagamento = form.tipo_pagamento.data
        cliente.limite_credito = form.limite_credito.data
        cliente.observacoes = form.observacoes.data
        
        db.session.commit()
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('clientes.detalhe_cliente', id=id))
    
    return render_template('clientes/novo.html', form=form, cliente=cliente)

@bp.route('/api/cliente/<int:id>/info')
@login_required
def cliente_info_api(id):
    """API para retornar informações do cliente em JSON"""
    cliente = Cliente.query.get_or_404(id)
    lista = []
    return jsonify({
        'username': cliente.nome,
        'limite': cliente.limite_credito,
        'saldo': cliente.saldo_devedor,
        'disponivel': cliente.limite_credito - cliente.saldo_devedor,
        'vendas': [venda.data_venda for venda in cliente.vendas]
    })