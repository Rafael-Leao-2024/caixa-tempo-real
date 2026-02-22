from flask import Flask
from config import Config
from app.extensoes import db, migrate, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """Obrigatório: carrega o usuário da base de dados pelo ID."""
        return User.query.get(int(user_id))
    

    # Configurar login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    # Registrar blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.clientes import bp as clientes_bp
    app.register_blueprint(clientes_bp, url_prefix='/clientes')

    from app.vendas import bp as vendas_bp
    app.register_blueprint(vendas_bp, url_prefix='/vendas')

    from app.relatorios import bp as relatorios_bp
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

    # Importar e registrar o blueprint de despesas

    # Depois dos outros imports de blueprints
    from app.produtos import bp as produtos_bp
    app.register_blueprint(produtos_bp)

    from app.despesas import bp as despesas_bp
    app.register_blueprint(despesas_bp)
    
    return app