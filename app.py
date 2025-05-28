# app.py

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from routes.whatsapp import whatsapp_bp

app = Flask(__name__)
app.register_blueprint(whatsapp_bp)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nutri_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua-secret-key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    
    current_flow = db.Column(db.String(50), nullable=True)
    flow_step = db.Column(db.Integer, default=0)
    
    email = db.Column(db.String(150), nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class Goal(db.Model):
    __tablename__ = "goals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_text = db.Column(db.String(200), nullable=False)

# class Checkin(db.Model):
#     ...
# class Reminder(db.Model):
#     ...
@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Recebe mensagens enviadas pelo usuário via Twilio (WhatsApp).
    """
    from_number = request.form.get('From')  # something como 'whatsapp:+5511999999999'
    body = request.form.get('Body')         # texto digitado pelo usuário
    
    if not body:
        body = ""  # Evitar erro se for None

    body_lower = body.strip().lower()

    user = User.query.filter_by(phone=from_number).first()

    if not user:
        user = User(phone=from_number, name="Novo Usuário")
        db.session.add(user)
        db.session.commit()
        send_whatsapp_message(from_number, "Olá! Você foi cadastrado automaticamente. Qual seu nome?")
        return jsonify({'status': 'new_user_created'})

    # Se o usuário já existe, verificamos se está em algum fluxo
    if user.current_flow == 'checkin':
        return handle_checkin_flow(user, body)

    if body_lower in ['menu', 'oi', 'olá', 'hello']:
        response_text = (
            "Olá! Selecione uma opção:\n"
            "1. Registrar consumo\n"
            "2. Consultar metas\n"
            "3. Iniciar check-in semanal"
        )
        send_whatsapp_message(from_number, response_text)
    
    elif body_lower == '1':
        # registrar consumo de água, etc.
        send_whatsapp_message(from_number, "Okay, vou registrar seu consumo. Quantos ml?")
    
    elif body_lower == '2':
        # Consultar metas do usuário
        goals = Goal.query.filter_by(user_id=user.id).all()
        if not goals:
            send_whatsapp_message(from_number, "Você não possui metas cadastradas.")
        else:
            metas = "\n".join([f"- {g.goal_text}" for g in goals])
            send_whatsapp_message(from_number, f"Sua(s) meta(s):\n{metas}")
    
    elif body_lower == '3':
        # Inicia o fluxo de check-in
        user.current_flow = 'checkin'
        user.flow_step = 1
        db.session.commit()
        send_whatsapp_message(from_number, "Vamos iniciar seu check-in! Pergunta 1: Como foi sua alimentação nesta semana?")
    
    else:
        send_whatsapp_message(from_number, "Digite 'menu' para ver as opções.")
    
    return jsonify({'status': 'success'})

def send_whatsapp_message(to_number, message_body):
    """
    Envia uma mensagem de texto simples via WhatsApp para o usuário.
    Este exemplo pode ser um mock ou a chamada real da Twilio.
    """

    print(f"[MOCK] Enviando WhatsApp para {to_number}: {message_body}")
    return "mock_message_id"

def handle_checkin_flow(user, body):
    """
    Lida com o fluxo de perguntas do check-in semanal.
    Dependendo do step em que o usuário está, faz perguntas ou finaliza.
    """
    from_number = user.phone
    step = user.flow_step

    if step == 1:
        print(f"[CHECKIN] Resposta da Pergunta 1: {body}")
        user.flow_step = 2
        db.session.commit()
        send_whatsapp_message(from_number, "Pergunta 2: Quanto tempo de exercício físico você fez essa semana?")
    
    elif step == 2:
        print(f"[CHECKIN] Resposta da Pergunta 2: {body}")
        user.flow_step = 3
        db.session.commit()
        send_whatsapp_message(from_number, "Pergunta 3: Você teve algum desafio ou dificuldade?")
    
    elif step == 3:
        print(f"[CHECKIN] Resposta da Pergunta 3: {body}")
        user.current_flow = None
        user.flow_step = 0
        db.session.commit()
        send_whatsapp_message(from_number, "Check-in finalizado! Obrigado pelas respostas.")
    
    return jsonify({'status': 'checkin_flow_handled'})

scheduler = BackgroundScheduler()

def send_weekly_checkin():
    """
    Envia mensagem de início de check-in para todos os usuários ativos
    que não estejam em um fluxo no momento.
    Dispara todo sábado às 09:00, por exemplo.
    """
    users = User.query.filter_by(is_active=True).all()
    for user in users:
        if not user.current_flow:
            user.current_flow = 'checkin'
            user.flow_step = 1
            db.session.commit()
            send_whatsapp_message(user.phone, "Olá! É hora do seu check-in semanal. Pergunta 1: Como foi sua alimentação?")
        else:
            print(f"[AGENDADOR] Usuário {user.phone} já está em um fluxo.")
    
def start_scheduler():
    """
    Inicia o APScheduler, definindo a tarefa de check-in semanal.
    """
    scheduler.add_job(send_weekly_checkin, 'cron', day_of_week='sat', hour=9, minute=0)
    
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()
    
    app.run(debug=True)
