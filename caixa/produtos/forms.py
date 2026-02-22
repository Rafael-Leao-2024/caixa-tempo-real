from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, Length

class ProdutoForm(FlaskForm):
    tipo = SelectField('Tipo de Placa', 
                      choices=[
                          ('placa_carro', 'Placa de Carro'),
                          ('placa_moto', 'Placa de Moto'),
                          ('placa_caminhao', 'Placa de Caminhão'),
                          ('outro', 'Outro')
                      ],
                      validators=[DataRequired()])
    
    descricao = StringField('Descrição', 
                           validators=[DataRequired(), Length(min=3, max=200)],
                           render_kw={"placeholder": "Ex: Placa Mercosul Padrão"})
    
    preco = FloatField('Preço (R$)', 
                      validators=[DataRequired(), NumberRange(min=0.01)],
                      render_kw={"placeholder": "0.00", "step": "0.01"})
    
    estoque = IntegerField('Estoque Inicial', 
                          validators=[Optional(), NumberRange(min=0)],
                          default=0,
                          render_kw={"placeholder": "0"})
    
    observacoes = TextAreaField('Observações', 
                               validators=[Optional()],
                               render_kw={"placeholder": "Informações adicionais sobre o produto..."})
    
    submit = SubmitField('Salvar Produto')

class ProdutoFilterForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[('', 'Todos')] + [
        ('placa_carro', 'Placa de Carro'),
        ('placa_moto', 'Placa de Moto'),
        ('placa_caminhao', 'Placa de Caminhão'),
        ('outro', 'Outro')
    ], validators=[Optional()])
    
    busca = StringField('Buscar', validators=[Optional()])
    submit = SubmitField('Filtrar')