#!/usr/bin/env python
"""Ponto de entrada da aplicação - Script para executar o servidor de desenvolvimento."""

import os
from dotenv import load_dotenv
from caixa import create_app

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Criar instância da aplicação
app = create_app()

if __name__ == '__main__':
    # Obter configurações do ambiente ou usar padrões
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', "5000"))
    
    # Executar aplicação
    app.run(
        debug=debug_mode,
        host="0.0.0.0",
        port=port
    )
    
    print(f"\n🚀 Servidor iniciado em http://{host}:{port}")
    print("👤 Use seu email Gmail para login")
    print("📝 Pressione CTRL+C para parar o servidor\n")