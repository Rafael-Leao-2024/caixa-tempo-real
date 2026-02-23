from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from caixa import db
from caixa.auth import bp
from caixa.auth.forms import LoginForm, RegisterCaixaForm
from caixa.models import User, Caixa
import os
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


# Configurações do Google OAuth
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/login/callback')


@bp.route('/login', methods=['GET'])
def login():
    """Página de login com botão do Google"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    google_auth_url = get_google_auth_url()
    return render_template('auth/login.html', 
                         google_auth_url=google_auth_url,
                         google_client_id=GOOGLE_CLIENT_ID, form=None)



def criar_caixa_automaticamente(user_id, nome_caixa):
    """Função para criar caixa automaticamente (pode ser chamada por script ou admin)"""
    caixa = Caixa(id=user_id, nome=nome_caixa, localizacao="Recife Placas")
    db.session.add(caixa)
    db.session.commit()
    db.session.refresh(caixa)
    return caixa

@bp.route('/login/callback')
def login_callback():
    """Callback após autenticação do Google"""
    code = request.args.get('code')
    
    if not code:
        flash('Falha na autenticação')
        return redirect(url_for('auth.login'))
    
    try:
        # Troca o código por um token
        token_response = exchange_code_for_token(code)
        
        # Valida o token e obtém informações do usuário
        user_info = validate_google_token(token_response['id_token'])
        # Obtém ou cria o usuário no banco de dados

        user = User.query.filter_by(id=user_info['sub'][-4:]).first()
        if not user:
            caixa = criar_caixa_automaticamente(user.id, nome_caixa=user.nome, caixa=caixa)

            user = User.get_or_create(
                id=user_info['sub'],
                nome=user_info['name'],
                email=user_info['email'],
                profile_pic=user_info.get('picture')
                
            )

            user.caixa_id = user.id
            db.session.commit()
            # Faz login do usuário
        login_user(user)
            
        flash('Login realizado com sucesso!', 'success')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        flash('Erro na autenticação exececional', 'danger')
        return redirect(url_for('auth.login'))

# funcoes auxiliares 
def get_google_auth_url():
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    
    params = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI'),
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    import urllib.parse
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    token_url = "https://oauth2.googleapis.com/token"
    
    data = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI')
    }
    
    response = requests.post(token_url, data=data)
    return response.json()

def validate_google_token(id_token_str):
    idinfo = id_token.verify_oauth2_token(
        id_token_str,
        google_requests.Request(),
        os.environ.get('GOOGLE_CLIENT_ID')
    )
    
    return idinfo

@bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    email = current_user.email
    logout_user()
    session.clear()
    flash(f'Você foi desconectado, {email}', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/register-caixa', methods=['GET', 'POST'])
@login_required
def register_caixa():
    """Rota existente para criar novos caixas (apenas proprietário)"""
    if not current_user.is_owner:
        flash('Apenas proprietários podem criar novos caixas.', 'danger')
        return redirect(url_for('main.index'))
    
    form = RegisterCaixaForm()
    if form.validate_on_submit():
        # Criar novo caixa
        caixa = Caixa(
            nome=form.nome_caixa.data,
            localizacao=form.localizacao.data
        )
        db.session.add(caixa)
        db.session.flush()
        
        # Criar usuário para o caixa (com senha para fallback)
        user = User(
            email=form.email.data,
            nome=form.nome_usuario.data,
            caixa_id=caixa.id,
            is_owner=False
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Caixa {caixa.nome} criado com sucesso!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('auth/register_caixa.html', form=form)
