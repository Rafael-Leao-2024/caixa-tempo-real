from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from caixa import db
from caixa.produtos import bp
from caixa.produtos.forms import ProdutoForm, ProdutoFilterForm
from caixa.models import Produto
from caixa.decoradores import caixa_required

@bp.route('/')
@login_required
@caixa_required
def lista_produtos():
    page = request.args.get('page', 1, type=int)
    tipo = request.args.get('tipo', '')
    busca = request.args.get('busca', '')
    
    query = Produto.query
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    if busca:
        query = query.filter(Produto.descricao.contains(busca))
    
    produtos = query.order_by(Produto.tipo, Produto.descricao).paginate(
        page=page, per_page=10, error_out=False
    )
    
    form = ProdutoFilterForm()
    
    return render_template('produtos/lista.html', 
                         produtos=produtos, 
                         form=form,
                         filtros={'tipo': tipo, 'busca': busca})

@bp.route('/novo', methods=['GET', 'POST'])
@login_required
@caixa_required
def novo_produto():
    form = ProdutoForm()
    
    if form.validate_on_submit():
        produto = Produto(
            tipo=form.tipo.data,
            descricao=form.descricao.data,
            preco=form.preco.data,
            estoque=form.estoque.data or 0
        )
        
        db.session.add(produto)
        db.session.commit()
        
        flash(f'Produto "{produto.descricao}" cadastrado com sucesso!', 'success')
        return redirect(url_for('produtos.lista_produtos'))
    
    return render_template('produtos/novo.html', form=form)

@bp.route('/<int:id>')
@login_required
@caixa_required
def detalhe_produto(id):
    produto = Produto.query.get_or_404(id)
    return render_template('produtos/detalhe.html', produto=produto)

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@caixa_required
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    form = ProdutoForm(obj=produto)
    
    if form.validate_on_submit():
        produto.tipo = form.tipo.data
        produto.descricao = form.descricao.data
        produto.preco = form.preco.data
        produto.estoque = form.estoque.data or 0
        
        db.session.commit()
        
        flash(f'Produto "{produto.descricao}" atualizado!', 'success')
        return redirect(url_for('produtos.detalhe_produto', id=id))
    
    return render_template('produtos/novo.html', form=form, produto=produto)

@bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
@caixa_required
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)
    
    # Verificar se há vendas associadas
    if produto.itens_venda.count() > 0:
        flash('Não é possível excluir produto com vendas associadas.', 'danger')
        return redirect(url_for('produtos.detalhe_produto', id=id))
    
    db.session.delete(produto)
    db.session.commit()
    
    flash(f'Produto "{produto.descricao}" excluído!', 'success')
    return redirect(url_for('produtos.lista_produtos'))

@bp.route('/api/lista')
@login_required
def api_lista_produtos():
    """API para retornar lista de produtos em JSON (usado nos selects)"""
    produtos = Produto.query.all()
    return jsonify([{
        'id': p.id,
        'descricao': p.descricao,
        'preco': p.preco,
        'tipo': p.tipo,
        'estoque': p.estoque
    } for p in produtos])

@bp.route('/api/<int:id>')
@login_required
def api_produto(id):
    """API para retornar dados de um produto específico"""
    produto = Produto.query.get_or_404(id)
    return jsonify({
        'id': produto.id,
        'descricao': produto.descricao,
        'preco': produto.preco,
        'tipo': produto.tipo,
        'estoque': produto.estoque
    })

@bp.route('/api/verificar-estoque/<int:id>')
@login_required
def verificar_estoque(id):
    """API para verificar estoque disponível"""
    produto = Produto.query.get_or_404(id)
    quantidade = request.args.get('quantidade', 1, type=int)
    
    disponivel = produto.estoque >= quantidade
    
    return jsonify({
        'disponivel': disponivel,
        'estoque_atual': produto.estoque,
        'quantidade_solicitada': quantidade
    })