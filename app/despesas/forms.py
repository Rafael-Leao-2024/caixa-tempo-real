from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, Length
from datetime import date

class DespesaForm(FlaskForm):
    descricao = StringField('Descrição', 
                           validators=[DataRequired(), Length(min=3, max=200)],
                           render_kw={"placeholder": "Ex: Conta de luz, Aluguel, Compra de material..."})
    
    valor = FloatField('Valor (R$)', 
                      validators=[DataRequired(), NumberRange(min=0.01)],
                      render_kw={"placeholder": "0.00", "step": "0.01"})
    
    data_despesa = DateField('Data da Despesa', 
                            validators=[DataRequired()],
                            default=date.today,
                            render_kw={"type": "date"})
    
    categoria_id = SelectField('Categoria', 
                              coerce=int,
                              validators=[DataRequired()],
                              render_kw={"class": "form-select"})
    
    forma_pagamento = SelectField('Forma de Pagamento',
                                 choices=[
                                     ('', 'Selecione...'),
                                     ('dinheiro', 'Dinheiro'),
                                     ('cartao', 'Cartão'),
                                     ('pix', 'PIX'),
                                     ('boleto', 'Boleto'),
                                     ('transferencia', 'Transferência')
                                 ],
                                 validators=[DataRequired()])
    
    observacoes = TextAreaField('Observações',
                               validators=[Optional()],
                               render_kw={"rows": "3", "placeholder": "Informações adicionais..."})
    
    submit = SubmitField('Salvar Despesa')


class CategoriaDespesaForm(FlaskForm):
    nome = StringField('Nome da Categoria', 
                      validators=[DataRequired(), Length(min=3, max=50)],
                      render_kw={"placeholder": "Ex: Contas, Matéria-prima, Marketing..."})
    
    descricao = StringField('Descrição',
                           validators=[Optional(), Length(max=200)],
                           render_kw={"placeholder": "Descrição opcional da categoria"})
    
    submit = SubmitField('Salvar Categoria')