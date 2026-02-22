from flask_wtf import FlaskForm
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, FloatField, TextAreaField, SubmitField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Optional

class ItemVendaForm(FlaskForm):
    class Meta:
        # Desabilitar CSRF para itens individuais
        csrf = False
    
    produto_id = SelectField('Produto', coerce=int, validators=[DataRequired()])
    quantidade = IntegerField('Quantidade', default=1, validators=[NumberRange(min=1)])

class VendaForm(FlaskForm):
    cliente_id = SelectField('Cliente', coerce=int, validators=[DataRequired()])
    tipo_pagamento = SelectField('Tipo de Pagamento', 
                                choices=[('vista', 'À Vista'), ('prazo', 'A Prazo')],
                                validators=[DataRequired()])
    itens = FieldList(FormField(ItemVendaForm), min_entries=1)
    observacoes = TextAreaField('Observações')
    submit = SubmitField('Registrar Venda')

class PagamentoForm(FlaskForm):
    valor = FloatField('Valor do Pagamento', validators=[DataRequired(), NumberRange(min=0.01)])
    forma_pagamento = SelectField('Forma de Pagamento',
                                 choices=[('dinheiro', 'Dinheiro'), 
                                        ('cartao', 'Cartão'),
                                        ('pix', 'PIX')],
                                 validators=[DataRequired()])
    observacoes = TextAreaField('Observações')
    submit = SubmitField('Registrar Pagamento')