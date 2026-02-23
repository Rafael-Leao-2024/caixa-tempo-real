from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from caixa import db
from caixa.despesas import bp
from caixa.despesas.forms import DespesaForm, CategoriaDespesaForm
from caixa.models import Despesa, CategoriaDespesa, Caixa
from datetime import datetime, date
from sqlalchemy import func

# ========== ROTAS DE DESPESAS ==========

@bp.route('/')
@login_required
def lista_despesas():
    """Lista todas as despesas com filtros"""
    page = request.args.get('page', 1, type=int)
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    categoria_id = request.args.get('categoria_id', 0, type=int)
    forma_pagamento = request.args.get('forma_pagamento', '')
    
    query = Despesa.query
    
    # Aplicar filtros
    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        query = query.filter(Despesa.data_despesa >= data_inicio_obj)
    
    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
        query = query.filter(Despesa.data_despesa <= data_fim_obj)
    
    if categoria_id > 0:
        query = query.filter_by(categoria_id=categoria_id)
    
    if forma_pagamento:
        query = query.filter_by(forma_pagamento=forma_pagamento)
    
    # Se for operador de caixa, filtrar por caixa
    if not current_user.is_owner and current_user.caixa_id:
        query = query.filter_by(caixa_id=current_user.caixa_id)
    
    # Ordenar por data (mais recentes primeiro)
    despesas = query.order_by(Despesa.data_despesa.desc(), Despesa.data_registro.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calcular totais
    total_periodo = db.session.query(func.sum(Despesa.valor)).filter(
        Despesa.data_despesa >= (data_inicio_obj if data_inicio else date(1900,1,1)),
        Despesa.data_despesa <= (data_fim_obj if data_fim else date(2100,12,31))
    ).scalar() or 0
    
    # Categorias para o filtro
    categorias = CategoriaDespesa.query.order_by('nome').all()
    
    return render_template('despesas/lista.html',
                         despesas=despesas,
                         categorias=categorias,
                         total_periodo=total_periodo,
                         filtros={
                             'data_inicio': data_inicio,
                             'data_fim': data_fim,
                             'categoria_id': categoria_id,
                             'forma_pagamento': forma_pagamento
                         })


@bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_despesa():
    """Registrar nova despesa"""
    form = DespesaForm()
    
    # Carregar categorias
    form.categoria_id.choices = [(c.id, c.nome) for c in CategoriaDespesa.query.order_by('nome').all()]
    
    if form.validate_on_submit():
        despesa = Despesa(
            descricao=form.descricao.data,
            valor=form.valor.data,
            data_despesa=form.data_despesa.data,
            categoria_id=form.categoria_id.data,
            forma_pagamento=form.forma_pagamento.data,
            observacoes=form.observacoes.data,
            usuario_id=current_user.id,
            caixa_id=current_user.caixa_id if not current_user.is_owner else None
        )
        
        db.session.add(despesa)
        db.session.commit()
        
        flash(f'✅ Despesa "{despesa.descricao}" registrada com sucesso!', 'success')
        return redirect(url_for('despesas.lista_despesas'))
    
    return render_template('despesas/nova.html', form=form)


@bp.route('/<int:id>')
@login_required
def detalhe_despesa(id):
    """Ver detalhes de uma despesa"""
    despesa = Despesa.query.get_or_404(id)
    return render_template('despesas/detalhe.html', despesa=despesa)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_despesa(id):
    """Editar uma despesa existente"""
    despesa = Despesa.query.get_or_404(id)
    form = DespesaForm(obj=despesa)
    
    # Carregar categorias
    form.categoria_id.choices = [(c.id, c.nome) for c in CategoriaDespesa.query.order_by('nome').all()]
    
    if form.validate_on_submit():
        despesa.descricao = form.descricao.data
        despesa.valor = form.valor.data
        despesa.data_despesa = form.data_despesa.data
        despesa.categoria_id = form.categoria_id.data
        despesa.forma_pagamento = form.forma_pagamento.data
        despesa.observacoes = form.observacoes.data
        
        db.session.commit()
        
        flash(f'✅ Despesa "{despesa.descricao}" atualizada!', 'success')
        return redirect(url_for('despesas.lista_despesas'))
    
    return render_template('despesas/editar.html', form=form, despesa=despesa)


@bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_despesa(id):
    """Excluir uma despesa"""
    despesa = Despesa.query.get_or_404(id)
    
    db.session.delete(despesa)
    db.session.commit()
    
    flash(f'✅ Despesa excluída!', 'success')
    return redirect(url_for('despesas.lista_despesas'))


# ========== ROTAS DE CATEGORIAS ==========

@bp.route('/categorias')
@login_required
def lista_categorias():
    """Listar categorias de despesa"""
    categorias = CategoriaDespesa.query.order_by('nome').all()
    return render_template('despesas/categorias.html', categorias=categorias)


@bp.route('/categorias/nova', methods=['GET', 'POST'])
@login_required
def nova_categoria():
    """Criar nova categoria"""
    form = CategoriaDespesaForm()
    
    if form.validate_on_submit():
        categoria = CategoriaDespesa(
            nome=form.nome.data,
            descricao=form.descricao.data
        )
        
        db.session.add(categoria)
        db.session.commit()
        
        flash(f'✅ Categoria "{categoria.nome}" criada!', 'success')
        return redirect(url_for('despesas.lista_categorias'))
    
    return render_template('despesas/nova_categoria.html', form=form)


@bp.route('/categorias/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_categoria(id):
    """Editar categoria"""
    categoria = CategoriaDespesa.query.get_or_404(id)
    form = CategoriaDespesaForm(obj=categoria)
    
    if form.validate_on_submit():
        categoria.nome = form.nome.data
        categoria.descricao = form.descricao.data
        
        db.session.commit()
        
        flash(f'✅ Categoria "{categoria.nome}" atualizada!', 'success')
        return redirect(url_for('despesas.lista_categorias'))
    
    return render_template('despesas/editar_categoria.html', form=form, categoria=categoria)


@bp.route('/categorias/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_categoria(id):
    """Excluir categoria (apenas se não tiver despesas)"""
    categoria = CategoriaDespesa.query.get_or_404(id)
    
    # Verificar se há despesas nesta categoria
    if len(categoria.despesas) > 0:
        flash('❌ Não é possível excluir categoria com despesas vinculadas!', 'danger')
        return redirect(url_for('despesas.lista_categorias'))
    
    db.session.delete(categoria)
    db.session.commit()
    
    flash(f'✅ Categoria "{categoria.nome}" excluída!', 'success')
    return redirect(url_for('despesas.lista_categorias'))


# ========== ROTAS DE RELATÓRIOS ==========

@bp.route('/resumo-diario')
@login_required
def resumo_diario():
    """Resumo de despesas do dia"""
    hoje = date.today()
    
    despesas_hoje = Despesa.query.filter(
        Despesa.data_despesa == hoje
    ).all()
    
    total_hoje = sum(d.valor for d in despesas_hoje)
    
    return jsonify({
        'data': hoje.strftime('%d/%m/%Y'),
        'total': total_hoje,
        'quantidade': len(despesas_hoje),
        'despesas': [{
            'id': d.id,
            'descricao': d.descricao,
            'valor': d.valor,
            'categoria': d.categoria.nome
        } for d in despesas_hoje]
    })


@bp.route('/faturamento-diario')
@login_required
def faturamento_diario():
    """Relatório de faturamento do dia (vendas - despesas)"""
    from caixa.models import Venda
    
    hoje = date.today()
    
    # Total de vendas do dia
    vendas_hoje = Venda.query.filter(
        func.date(Venda.data_venda) == hoje
    ).all()
    total_vendas = sum(v.valor_total for v in vendas_hoje)
    
    # Total de despesas do dia
    despesas_hoje = Despesa.query.filter(
        Despesa.data_despesa == hoje
    ).all()
    total_despesas = sum(d.valor for d in despesas_hoje)
    
    # Resultado líquido
    resultado_liquido = total_vendas - total_despesas
    
    return jsonify({
        'data': hoje.strftime('%d/%m/%Y'),
        'vendas': total_vendas,
        'despesas': total_despesas,
        'resultado': resultado_liquido,
        'status': 'positivo' if resultado_liquido >= 0 else 'negativo'
    })