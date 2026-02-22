from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from caixa import db
from caixa.vendas import bp
from caixa.vendas.forms import VendaForm, PagamentoForm
from caixa.models import Cliente, Produto, Venda, ItemVenda, Pagamento, FluxoCaixa, Caixa
from caixa.decoradores import caixa_required
from datetime import datetime, date

# ========== FUNÇÕES AUXILIARES DO FLUXO DE CAIXA ==========

def atualizar_fluxo_caixa(data, caixa_id=None):
    """
    Atualiza ou cria o registro de fluxo de caixa para uma data específica
    """
    # Se não especificar caixa, usar o caixa do usuário atual
    if not caixa_id and not current_user.is_owner:
        caixa_id = current_user.caixa_id
    
    # Buscar ou criar fluxo de caixa para esta data
    fluxo = FluxoCaixa.query.filter_by(
        data=data,
        caixa_id=caixa_id
    ).first()
    
    if not fluxo:
        fluxo = FluxoCaixa(
            data=data,
            saldo_inicial=0,
            total_vendas_vista=0,
            total_vendas_prazo=0,
            total_recebimentos=0,
            saldo_final=0,
            caixa_id=caixa_id
        )
        db.session.add(fluxo)
    
    # Recalcular todos os valores do dia
    vendas_dia = Venda.query.filter(
        db.func.date(Venda.data_venda) == data
    )
    if caixa_id:
        vendas_dia = vendas_dia.filter_by(caixa_id=caixa_id)
    vendas_dia = vendas_dia.all()
    
    # Calcular totais de vendas
    total_vista = sum(v.valor_total for v in vendas_dia if v.tipo_pagamento == 'vista')
    total_prazo = sum(v.valor_total for v in vendas_dia if v.tipo_pagamento == 'prazo')
    
    # Calcular recebimentos do dia (pagamentos)
    pagamentos_dia = Pagamento.query.join(Venda).filter(
        db.func.date(Pagamento.data_pagamento) == data
    )
    if caixa_id:
        pagamentos_dia = pagamentos_dia.filter(Venda.caixa_id == caixa_id)
    pagamentos_dia = pagamentos_dia.all()
    
    total_recebimentos = sum(p.valor for p in pagamentos_dia)
    
    # Atualizar fluxo
    fluxo.total_vendas_vista = total_vista
    fluxo.total_vendas_prazo = total_prazo
    fluxo.total_recebimentos = total_recebimentos
    
    # Calcular saldo final (saldo_inicial + recebimentos)
    # Nota: saldo_inicial pode ser ajustado manualmente ou vir do dia anterior
    fluxo.saldo_final = fluxo.saldo_inicial + total_recebimentos
    
    return fluxo


def atualizar_fluxo_mes(data_inicio, data_fim, caixa_id=None):
    """
    Atualiza o fluxo de caixa para um período
    """
    from datetime import timedelta
    
    data_atual = data_inicio
    while data_atual <= data_fim:
        atualizar_fluxo_caixa(data_atual, caixa_id)
        data_atual += timedelta(days=1)
    
    db.session.commit()


@bp.route('/nova', methods=['GET', 'POST'])
@login_required
@caixa_required
def nova_venda():
    print("="*50)
    print("ENTROU NA ROTA NOVA VENDA")
    print(f"Método: {request.method}")
    print(f"Form data: {request.form}")
    print("="*50)
    
    form = VendaForm()
    
    # Carregar opções para selects
    form.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.order_by('nome').all()]
    
    # Carregar produtos para os itens
    produtos = Produto.query.all()
    for item in form.itens:
        item.produto_id.choices = [(p.id, f"{p.descricao} - R$ {p.preco:.2f}") for p in produtos]
    
    # SE FOR POST - FINALIZAR A VENDA
    if request.method == 'POST':
        print("🔍 PROCESSANDO POST")
        print(f"Form validate: {form.validate()}")
        print(f"Errors: {form.errors}")
        
        if form.validate_on_submit():
            print("✅ FORMULÁRIO VÁLIDO")
            try:
                # Calcular valor total
                valor_total = 0
                itens_venda = []
                
                print(f"Dados do form: {form.data}")
                
                # Processar itens do formulário
                for idx, item in enumerate(form.itens.data):
                    print(f"Item {idx}: {item}")
                    produto = Produto.query.get(item['produto_id'])
                    if produto:
                        subtotal = produto.preco * item['quantidade']
                        valor_total += subtotal
                        itens_venda.append({
                            'produto': produto,
                            'quantidade': item['quantidade'],
                            'preco': produto.preco,
                            'subtotal': subtotal
                        })
                        print(f"Produto: {produto.descricao}, Qtd: {item['quantidade']}, Preço: {produto.preco}")
                
                print(f"Valor total calculado: {valor_total}")
                
                # Verificar estoque
                for item in itens_venda:
                    if item['produto'].estoque < item['quantidade']:
                        print(f"⚠️ Estoque insuficiente para {item['produto'].descricao}")
                        flash(f'Estoque insuficiente para {item["produto"].descricao}', 'danger')
                        return render_template('vendas/nova.html', form=form)
                
                # Verificar limite de crédito
                cliente = Cliente.query.get(form.cliente_id.data)
                print(f"Cliente: {cliente.nome if cliente else 'None'}")
                
                if form.tipo_pagamento.data == 'prazo':
                    if cliente.saldo_devedor + valor_total > cliente.limite_credito:
                        print("⚠️ Limite de crédito excedido")
                        flash('Cliente excedeu o limite de crédito!', 'danger')
                        return render_template('vendas/nova.html', form=form)
                
                # CRIAR A VENDA
                print("📝 Criando venda...")
                data_venda = datetime.now()
                venda = Venda(
                    data_venda=data_venda,
                    valor_total=valor_total,
                    tipo_pagamento=form.tipo_pagamento.data,
                    status='pendente' if form.tipo_pagamento.data == 'prazo' else 'pago',
                    cliente_id=form.cliente_id.data,
                    vendedor_id=current_user.id,
                    caixa_id=current_user.id,
                    observacoes=form.observacoes.data
                )
                
                if form.tipo_pagamento.data == 'vista':
                    venda.valor_pago = valor_total
                    venda.status = 'pago'
                
                db.session.add(venda)
                db.session.flush()
                print(f"Venda ID: {venda.id}")
                
                # Adicionar itens
                for item in itens_venda:
                    item_venda = ItemVenda(
                        venda_id=venda.id,
                        produto_id=item['produto'].id,
                        quantidade=item['quantidade'],
                        preco_unitario=item['preco'],
                        subtotal=item['subtotal']
                    )
                    db.session.add(item_venda)
                    print(f"Item adicionado: {item['produto'].descricao}")
                    
                    # Atualizar estoque
                    item['produto'].estoque -= item['quantidade']
                
                # Registrar pagamento se à vista
                if form.tipo_pagamento.data == 'vista':
                    pagamento = Pagamento(
                        venda_id=venda.id,
                        valor=valor_total,
                        forma_pagamento='dinheiro',
                        recebedor_id=current_user.id,
                        data_pagamento=data_venda
                    )
                    db.session.add(pagamento)
                    print("Pagamento registrado")
                
                # Atualizar saldo do cliente se a prazo
                if form.tipo_pagamento.data == 'prazo':
                    cliente.saldo_devedor += valor_total
                    print(f"Saldo do cliente atualizado: {cliente.saldo_devedor}")
                
                # ===== ATUALIZAR FLUXO DE CAIXA =====
                data_hoje = data_venda.date()
                atualizar_fluxo_caixa(data_hoje, current_user.id)
                print(f"✅ Fluxo de caixa atualizado para {data_hoje}")
                
                # Commit final
                db.session.commit()
                print("✅ COMMIT REALIZADO COM SUCESSO!")
                
                # Verificar se a venda foi realmente salva
                venda_verificacao = Venda.query.get(venda.id)
                if venda_verificacao:
                    print(f"✅ Venda {venda.id} encontrada no banco!")
                else:
                    print("❌ Venda NÃO encontrada no banco após commit!")
                
                flash(f'Venda finalizada com sucesso! Valor: R$ {valor_total:.2f}', 'success')
                return redirect(url_for('vendas.detalhe_venda', id=venda.id))
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ ERRO: {str(e)}")
                import traceback
                traceback.print_exc()
                flash(f'Erro ao finalizar venda: {str(e)}', 'danger')
                return render_template('vendas/nova.html', form=form)
        else:
            print(f"❌ Formulário inválido: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'danger')
    
    # SE FOR GET - MOSTRAR FORMULÁRIO
    return render_template('vendas/nova.html', form=form)


@bp.route('/<int:id>')
@login_required
@caixa_required
def detalhe_venda(id):
    venda = Venda.query.get_or_404(id)
    return render_template('vendas/detalhe.html', venda=venda)


@bp.route('/<int:id>/pagar', methods=['GET', 'POST'])
@login_required
@caixa_required
def registrar_pagamento(id):
    venda = Venda.query.get_or_404(id)
    form = PagamentoForm()
    
    if form.validate_on_submit():
        valor_restante = venda.valor_total - venda.valor_pago
        
        if form.valor.data > valor_restante:
            flash('Valor do pagamento excede o valor restante da venda!', 'danger')
            return render_template('vendas/pagamento.html', form=form, venda=venda)
        
        # Registrar pagamento
        data_pagamento = datetime.now()
        pagamento = Pagamento(
            venda_id=venda.id,
            valor=form.valor.data,
            forma_pagamento=form.forma_pagamento.data,
            recebedor_id=current_user.id,
            observacoes=form.observacoes.data,
            data_pagamento=data_pagamento
        )
        db.session.add(pagamento)
        
        # Atualizar venda
        venda.valor_pago += form.valor.data
        
        status_anterior = venda.status
        
        if venda.valor_pago >= venda.valor_total:
            venda.status = 'pago'
            venda.valor_pago = venda.valor_total
            
            # Atualizar saldo do cliente
            cliente = Cliente.query.get(venda.cliente_id)
            cliente.saldo_devedor -= venda.valor_total
        
        # ===== ATUALIZAR FLUXO DE CAIXA =====
        data_hoje = data_pagamento.date()
        atualizar_fluxo_caixa(data_hoje, current_user.id)
        print(f"✅ Fluxo de caixa atualizado para {data_hoje}")
        
        db.session.commit()
        
        flash('Pagamento registrado com sucesso!', 'success')
        return redirect(url_for('vendas.detalhe_venda', id=venda.id))
    
    return render_template('vendas/pagamento.html', form=form, venda=venda)


@bp.route('/ativas')
@login_required
@caixa_required
def vendas_ativas():
    vendas = Venda.query.filter(Venda.status != 'pago').order_by(Venda.data_venda.desc()).all()
    return render_template('vendas/lista.html', vendas=vendas, titulo='Vendas Ativas')


@bp.route('/todas')
@login_required
@caixa_required
def todas_vendas():
    page = request.args.get('page', 1, type=int)
    vendas = Venda.query.order_by(Venda.data_venda.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('vendas/lista.html', vendas=vendas, titulo='Todas as Vendas')


@bp.route('/api/venda/<int:id>/detalhes')
@login_required
def venda_detalhes_api(id):
    """API para retornar detalhes da venda em JSON"""
    venda = Venda.query.get_or_404(id)
    
    status_cores = {
        'pago': 'success',
        'pendente': 'warning',
        'parcial': 'info'
    }
    
    return jsonify({
        'cliente': venda.cliente.nome,
        'data': venda.data_venda.strftime('%d/%m/%Y %H:%M'),
        'valor_total': f"{venda.valor_total:.2f}",
        'valor_pago': f"{venda.valor_pago:.2f}",
        'status': venda.status,
        'status_cor': status_cores.get(venda.status, 'secondary'),
        'itens': [{
            'produto': item.produto.descricao,
            'quantidade': item.quantidade,
            'preco': f"{item.preco_unitario:.2f}"
        } for item in venda.itens]
    })


# ===== ROTAS PARA RECALCULAR FLUXO DE CAIXA (ADMIN) =====
@bp.route('/recalcular-fluxo/<string:data>')
@login_required
def recalcular_fluxo_data(data):
    """Recalcular fluxo de caixa para uma data específica (apenas owner)"""
    if not current_user.is_owner:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_obj = datetime.strptime(data, '%Y-%m-%d').date()
        
        # Recalcular para todos os caixas
        caixas = Caixa.query.all()
        for caixa in caixas:
            atualizar_fluxo_caixa(data_obj, caixa.id)
        
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Fluxo de caixa recalculado para {data_obj.strftime("%d/%m/%Y")}'
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 400


@bp.route('/recalcular-fluxo-periodo')
@login_required
def recalcular_fluxo_periodo():
    """Recalcular fluxo de caixa para um período (apenas owner)"""
    if not current_user.is_owner:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    if not data_inicio or not data_fim:
        return jsonify({'erro': 'Datas não fornecidas'}), 400
    
    try:
        inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        
        caixas = Caixa.query.all()
        for caixa in caixas:
            atualizar_fluxo_mes(inicio, fim, caixa.id)
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Fluxo de caixa recalculado de {inicio.strftime("%d/%m/%Y")} a {fim.strftime("%d/%m/%Y")}'
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 400