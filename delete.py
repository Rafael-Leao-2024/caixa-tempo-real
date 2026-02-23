from caixa.models import Venda, db, Pagamento
from caixa import create_app

app = create_app()

with app.app_context():
    venda = Venda.query.filter(Venda.id == 11).first()
    # venda = Pagamento.query.filter(Pagamento.venda_id == 11).first()
    db.session.delete(venda)
    db.session.commit()

