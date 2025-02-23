# app.py

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from routes.whatsapp import whatsapp_bp

# ========== CONFIGURAÇÃO BÁSICA DO FLASK & DB ==========
app = Flask(__name__)
# Exemplo de conexão local. Ajuste para o seu banco real:
app.register_blueprint(whatsapp_bp)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nutri_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua-secret-key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ========== MODELO DE USUÁRIO ========== 
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    
    # Colunas para controle de fluxo conversacional:
    current_flow = db.Column(db.String(50), nullable=True)
    flow_step = db.Column(db.Integer, default=0)
    
    # Exemplo: colunas de autenticação
    email = db.Column(db.String(150), nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

# Exemplo de outro modelo para Goals, Checkins etc. (Opcional)
class Goal(db.Model):
    __tablename__ = "goals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_text = db.Column(db.String(200), nullable=False)

# Caso precise de Checkin, Reminders etc., crie modelos semelhantes:
# class Checkin(db.Model):
#     ...
# class Reminder(db.Model):
#     ...

# ========== (1) REMOÇÃO/ADAPTAÇÃO DO PAINEL ADMIN ========== 
# Se antes existia algo como:
#
# @app.route('/admin')
# def admin_panel():
#     # Renderizava template jinja2
#     # Vamos comentar/remover para focar no fluxo WhatsApp
#     pass
#
# Simplesmente REMOVA ou COMENTE esse trecho.


# ========== (2) CRIAR ROTA /WEBHOOK/WHATSAPP PARA RECEBER MENSAGENS ==========

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Recebe mensagens enviadas pelo usuário via Twilio (WhatsApp).
    """
    # Twilio geralmente envia dados via form-encoded:
    from_number = request.form.get('From')  # something como 'whatsapp:+5511999999999'
    body = request.form.get('Body')         # texto digitado pelo usuário
    
    if not body:
        body = ""  # Evitar erro se for None

    # Limpamos e deixamos em lowercase para comparar
    body_lower = body.strip().lower()

    # Buscamos o usuário no BD pelo número
    user = User.query.filter_by(phone=from_number).first()

    if not user:
        # Se não achou, você decide se cadastra automaticamente ou avisa o usuário
        # Para teste, vamos criar o usuário "on the fly"
        user = User(phone=from_number, name="Novo Usuário")
        db.session.add(user)
        db.session.commit()
        send_whatsapp_message(from_number, "Olá! Você foi cadastrado automaticamente. Qual seu nome?")
        return jsonify({'status': 'new_user_created'})

    # Se o usuário já existe, verificamos se está em algum fluxo
    if user.current_flow == 'checkin':
        return handle_checkin_flow(user, body)

    # Caso não esteja em fluxo nenhum, oferecemos um menu simples
    if body_lower in ['menu', 'oi', 'olá', 'hello']:
        response_text = (
            "Olá! Selecione uma opção:\n"
            "1. Registrar consumo\n"
            "2. Consultar metas\n"
            "3. Iniciar check-in semanal"
        )
        send_whatsapp_message(from_number, response_text)
    
    elif body_lower == '1':
        # Exemplo: registrar consumo de água, etc.
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

# ========== (3) FUNÇÃO DE ENVIO DE MENSAGEM VIA WHATSAPP ==========
def send_whatsapp_message(to_number, message_body):
    """
    Envia uma mensagem de texto simples via WhatsApp para o usuário.
    Este exemplo pode ser um mock ou a chamada real da Twilio.
    """
    # Se for usar Twilio real, descomente e configure:
    #
    # from twilio.rest import Client
    # account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    # auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    # client = Client(account_sid, auth_token)
    #
    # message = client.messages.create(
    #     from_='whatsapp:+SEU_NUMERO_TWILIO',
    #     body=message_body,
    #     to=to_number  # lembre de incluir 'whatsapp:' se necessário (ex: f'whatsapp:{to_number}')
    # )
    #
    # return message.sid

    # Por enquanto, exibe no console (mock):
    print(f"[MOCK] Enviando WhatsApp para {to_number}: {message_body}")
    return "mock_message_id"

# ========== (4) FLUXO DE CHECK-IN ==========

def handle_checkin_flow(user, body):
    """
    Lida com o fluxo de perguntas do check-in semanal.
    Dependendo do step em que o usuário está, faz perguntas ou finaliza.
    """
    from_number = user.phone
    step = user.flow_step

    # Exemplo simples de 3 perguntas (pode estender para 10)
    if step == 1:
        # Resposta do usuário para a pergunta 1
        # Salva no BD se quiser, ex: user_checkin_info. Por simplicidade, só imprimimos
        print(f"[CHECKIN] Resposta da Pergunta 1: {body}")
        # Avança para a próxima pergunta
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
        # Finaliza
        user.current_flow = None
        user.flow_step = 0
        db.session.commit()
        send_whatsapp_message(from_number, "Check-in finalizado! Obrigado pelas respostas.")
    
    return jsonify({'status': 'checkin_flow_handled'})

# ========== (5) AGENDAMENTO DE MENSAGENS ==========
scheduler = BackgroundScheduler()

def send_weekly_checkin():
    """
    Envia mensagem de início de check-in para todos os usuários ativos
    que não estejam em um fluxo no momento.
    Dispara todo sábado às 09:00, por exemplo.
    """
    users = User.query.filter_by(is_active=True).all()
    for user in users:
        # Se o usuário não estiver em fluxo, iniciamos o check-in
        if not user.current_flow:
            user.current_flow = 'checkin'
            user.flow_step = 1
            db.session.commit()
            send_whatsapp_message(user.phone, "Olá! É hora do seu check-in semanal. Pergunta 1: Como foi sua alimentação?")
        else:
            # Se já está em algum fluxo, podemos ignorar ou tratar de outra forma
            print(f"[AGENDADOR] Usuário {user.phone} já está em um fluxo.")
    
def start_scheduler():
    """
    Inicia o APScheduler, definindo a tarefa de check-in semanal.
    """
    # Exemplo de agendamento: todo sábado às 9h
    scheduler.add_job(send_weekly_checkin, 'cron', day_of_week='sat', hour=9, minute=0)
    
    scheduler.start()

# ========== APP RUN ==========

if __name__ == "__main__":
    # Inicia o agendador
    start_scheduler()
    
    # Roda a aplicação Flask
    app.run(debug=True)
