from datetime import datetime, timedelta
from flask_login import UserMixin
from caixa.extensoes import db
from zoneinfo import ZoneInfo

def agora_brasil():
    return datetime.now(ZoneInfo("America/Sao_Paulo")) - timedelta(hours=3)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    is_owner = db.Column(db.Boolean, default=True)
    caixa_id = db.Column(db.Integer, db.ForeignKey('caixas.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=agora_brasil)
    
    # Campos para Google OAuth
    profile_pic = db.Column(db.String(500), nullable=True, default='https://www.gravatar.com/avatar/?d=mp&s=200')
    password_hash = db.Column(db.String(200), nullable=False, default='1234')  # Para fallback de login local
    
    # CORREÇÃO 1: Especificar foreign_keys no relacionamento
    caixa = db.relationship('Caixa', 
                           foreign_keys=[caixa_id],  # <-- IMPORTANTE
                           back_populates='usuarios',  # <-- Usar back_populates em vez de backref
                           lazy=True)
    
    vendas = db.relationship('Venda', backref='vendedor', foreign_keys='Venda.vendedor_id', lazy=True, cascade='all, delete-orphan')
    pagamentos_recebidos = db.relationship('Pagamento', backref='recebedor', foreign_keys='Pagamento.recebedor_id', lazy=True)
    
    @staticmethod
    def get_or_create(id, nome, email, profile_pic):
        user = User.query.get(id[-4:])
        if not user:
            user = User(
                id=id[-4:],
                email=email,
                nome=nome,
                is_owner=True,
                caixa_id='1234',
                profile_pic=profile_pic,
                password_hash='1234'
            )
            db.session.add(user)
            db.session.commit()
        return user

class Caixa(db.Model):
    __tablename__ = 'caixas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    localizacao = db.Column(db.String(200), nullable=False, default='Loja Principal')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=agora_brasil)
    
    # CORREÇÃO 2: Remover owner_id para quebrar o ciclo
    # Em vez disso, o relacionamento é feito via User.caixa_id
    
    # Relacionamento corrigido
    usuarios = db.relationship('User', 
                              foreign_keys='User.caixa_id',  # <-- IMPORTANTE
                              back_populates='caixa',
                              lazy=True)
    
    vendas = db.relationship('Venda', backref='caixa_local', foreign_keys='Venda.caixa_id', lazy=True)

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    tipo_pagamento = db.Column(db.String(20), default='vista')
    limite_credito = db.Column(db.Float, default=100000.00)
    saldo_devedor = db.Column(db.Float, default=0)
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=agora_brasil)
    
    vendas = db.relationship('Venda', backref='cliente', foreign_keys='Venda.cliente_id', lazy=True)

class Produto(db.Model):
    __tablename__ = 'produtos'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(200))
    preco = db.Column(db.Float, nullable=False)
    estoque = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=agora_brasil)
    
    itens_venda = db.relationship('ItemVenda', backref='produto', lazy=True)

class Venda(db.Model):
    __tablename__ = 'vendas'
    
    id = db.Column(db.Integer, primary_key=True)
    data_venda = db.Column(db.DateTime, default=agora_brasil)
    valor_total = db.Column(db.Float, nullable=False)
    valor_pago = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='pendente')
    tipo_pagamento = db.Column(db.String(20))
    observacoes = db.Column(db.Text)
    
    # Chaves estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    caixa_id = db.Column(db.Integer, db.ForeignKey('caixas.id'))
    
    # Relacionamentos com foreign_keys especificadas
    itens = db.relationship('ItemVenda', backref='venda', lazy=True, cascade='all, delete-orphan')
    pagamentos = db.relationship('Pagamento', backref='venda', lazy=True)

class ItemVenda(db.Model):
    __tablename__ = 'itens_venda'
    
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    preco_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

class Pagamento(db.Model):
    __tablename__ = 'pagamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_pagamento = db.Column(db.DateTime, default=agora_brasil)
    forma_pagamento = db.Column(db.String(50))
    recebedor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    observacoes = db.Column(db.Text)

class FluxoCaixa(db.Model):
    __tablename__ = 'fluxo_caixa'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    saldo_inicial = db.Column(db.Float, default=0)
    total_vendas_vista = db.Column(db.Float, default=0)
    total_vendas_prazo = db.Column(db.Float, default=0)
    total_recebimentos = db.Column(db.Float, default=0)
    saldo_final = db.Column(db.Float, default=0)
    caixa_id = db.Column(db.Integer, db.ForeignKey('caixas.id'))

     # RELACIONAMENTO - É ISSO QUE PERMITE acessar fluxo.caixa.nome
    caixa = db.relationship('Caixa', backref=db.backref('fluxos', lazy='dynamic'))


class CategoriaDespesa(db.Model):
    __tablename__ = 'categorias_despesa'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=agora_brasil)
    
    # Relacionamentos
    despesas = db.relationship('Despesa', backref='categoria', lazy=True)


class Despesa(db.Model):
    __tablename__ = 'despesas'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_despesa = db.Column(db.Date, nullable=False, default=agora_brasil)
    data_registro = db.Column(db.DateTime, default=agora_brasil)
    forma_pagamento = db.Column(db.String(50))  # 'dinheiro', 'cartao', 'pix', 'boleto'
    observacoes = db.Column(db.Text)
    
    # Chaves estrangeiras
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_despesa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    caixa_id = db.Column(db.Integer, db.ForeignKey('caixas.id'), nullable=True)
    
    # Relacionamentos
    usuario = db.relationship('User', backref='despesas')
    caixa = db.relationship('Caixa', backref='despesas')