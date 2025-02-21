from project.extensions import db
from datetime import datetime, timedelta

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    peso = db.Column(db.Float, nullable=False)
    altura = db.Column(db.Float, nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(120), nullable=False)  # Guardar hash da senha
    acesso_expira = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(weeks=2))

    def acesso_valido(self):
        return datetime.utcnow() < self.acesso_expira

    def calcular_imc(self):
        return self.peso / ((self.altura / 100) ** 2)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tipo = db.Column(db.String(50), nullable=False)
    frequencia = db.Column(db.Integer, nullable=False)
    concluido = db.Column(db.Boolean, default=False)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    texto = db.Column(db.String(200), nullable=False)
    horario = db.Column(db.Time, nullable=False)
    repeticao = db.Column(db.String(20), default='diario')

class CheckinResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    data = db.Column(db.DateTime, default=datetime.utcnow)
    pergunta = db.Column(db.String(200), nullable=False)
    resposta = db.Column(db.String(500))
