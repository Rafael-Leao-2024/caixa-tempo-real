from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, NumberRange

class ClienteForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    telefone = StringField('Telefone')
    email = StringField('Email', validators=[Optional(), Email()])
    tipo_pagamento = SelectField('Tipo de Pagamento', 
                                choices=[('vista', 'À Vista'), ('prazo', 'A Prazo')],
                                validators=[DataRequired()])
    limite_credito = FloatField('Limite de Crédito', default=100000.00, 
                               validators=[NumberRange(min=0)])
    observacoes = TextAreaField('Observações')
    submit = SubmitField('Salvar')