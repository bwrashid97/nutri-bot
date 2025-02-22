from datetime import datetime, timedelta
from project.extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    peso = db.Column(db.Float, nullable=False)
    altura = db.Column(db.Float, nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    access_expiration = db.Column(db.DateTime, nullable=False,
                                  default=lambda: datetime.utcnow() + timedelta(days=14))  # Por exemplo, 2 semanas

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "peso": self.peso,
            "altura": self.altura,
            "idade": self.idade,
            "email": self.email,
            "access_expiration": self.access_expiration.isoformat()
        }

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    meta_semana = db.Column(db.String(255), nullable=True)  # Por exemplo, "3 treinos, 2 dietas"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "descricao": self.descricao,
            "meta_semana": self.meta_semana,
            "created_at": self.created_at.isoformat()
        }

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mensagem = db.Column(db.String(255), nullable=False)
    # Armazenar o intervalo desejado (ex.: "4 horas")
    intervalo = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "mensagem": self.mensagem,
            "intervalo": self.intervalo,
            "created_at": self.created_at.isoformat()
        }

class Checkin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    respostas = db.Column(db.JSON, nullable=False)  # Armazena as respostas do check-in semanal
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "respostas": self.respostas,
            "created_at": self.created_at.isoformat()
        }

# Opcional: Modelo para registrar consumo de água diário
class WaterConsumption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    quantidade = db.Column(db.Integer, default=0)  # Em ml

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "data": self.data.isoformat(),
            "quantidade": self.quantidade
        }
