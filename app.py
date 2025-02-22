import os
import openai
from datetime import datetime
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from project.config import Config
from project.extensions import db
from twilio.rest import Client  # Para integração real (usado se MOCK_INTEGRATIONS=False)

# Import dos blueprints REST
from project.routes.auth import auth_bp
from project.routes.goals import goals_bp
from project.routes.reminders import reminders_bp
from project.routes.checkin import checkin_bp

def get_diet_response(user_question):
    if Config.MOCK_INTEGRATIONS:
        return f"Resposta simulada para: '{user_question}'"
    openai.api_key = Config.OPENAI_API_KEY
    prompt = (
        "O plano de dieta da cliente inclui receitas low-carb, substituições para carboidratos, "
        "e links específicos: https://www.exemplo.com/receitas-saudaveis e https://www.exemplo.com/dicas-dieta.\n"
        f"Pergunta: {user_question}\nResposta:"
    )
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].text.strip()

def get_training_tip(prompt):
    if Config.MOCK_INTEGRATIONS:
        return f"Dica simulada para: '{prompt}'"
    openai.api_key = Config.OPENAI_API_KEY
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=50
    )
    return response.choices[0].text.strip()

def send_sms(to, message):
    if Config.MOCK_INTEGRATIONS:
        return "fake_sms_sid"
    if not all([Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN, Config.TWILIO_WHATSAPP_NUMBER]):
        raise Exception("Twilio não configurado.")
    client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
    sms = client.messages.create(
        body=message,
        from_=Config.TWILIO_WHATSAPP_NUMBER,
        to=to
    )
    return sms.sid

def send_interactive_message(to, text):
    """
    Envia uma mensagem interativa (ou simula) para o número 'to'.
    No modo MOCK, apenas imprime no console.
    """
    if Config.MOCK_INTEGRATIONS:
        print(f"[MOCK] Enviando para {to}: {text}")
        return "fake_interactive_sid"
    client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        from_=Config.TWILIO_WHATSAPP_NUMBER,
        to=to,
        body=text
    )
    return message.sid

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)
    
    # Registro dos blueprints REST
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(goals_bp, url_prefix='/goals')
    app.register_blueprint(reminders_bp, url_prefix='/reminders')
    app.register_blueprint(checkin_bp, url_prefix='/checkin')
    
    @app.route('/')
    def index():
        return "Bot WhatsApp rodando!"
    
    # Webhook para mensagens do WhatsApp
    @app.route('/webhook/whatsapp', methods=['POST'])
    def whatsapp_webhook():
        from_number = request.form.get('From')  # Exemplo: 'whatsapp:+551199999999'
        body = request.form.get('Body')           # Texto digitado ou payload do botão
        
        # Número do administrador (fluxo administrativo)
        admin_number = "whatsapp:+5511999999999"
        if from_number == admin_number:
            response_text = process_admin_message(body, from_number)
        else:
            response_text = process_user_message(body, from_number)
        
        send_interactive_message(from_number, response_text)
        return "OK", 200
    
    def process_admin_message(body, from_number):
        lower_body = body.strip().lower()
        if lower_body in ["1", "usuarios"]:
            from project.models import User
            users = User.query.all()
            msg = "Lista de Usuários:\n"
            for u in users:
                days_left = (u.access_expiration - datetime.utcnow()).days
                msg += f"{u.nome} ({u.email}): {days_left} dias restantes\n"
            return msg
        elif lower_body in ["2", "reativar"]:
            return "Por favor, informe o email do usuário a reativar."
        else:
            return ("Olá, admin! Escolha uma opção:\n"
                    "1. Ver usuários\n"
                    "2. Reativar usuário\n"
                    "Envie o número correspondente.")
    
    def process_user_message(body, from_number):
        lower_body = body.strip().lower()
        if lower_body in ["+500ml", "add_500"]:
            # Lógica para atualizar o consumo de água do usuário (a ser implementada)
            return "Você adicionou 500ml ao seu consumo hoje. Continue assim!"
        elif lower_body in ["+1000ml", "add_1000"]:
            return "Você adicionou 1000ml ao seu consumo hoje. Continue assim!"
        elif lower_body in ["menu", "início"]:
            return ("Olá! Escolha uma opção:\n"
                    "1. Registrar consumo de água\n"
                    "2. Definir/Editar metas\n"
                    "3. Realizar check-in semanal\n"
                    "4. Consultar dicas de treino/dieta\n"
                    "Envie o número correspondente ou clique no botão adequado.")
        elif lower_body in ["cancel", "voltar", "refazer"]:
            return "Voltando ao menu principal. Por favor, escolha uma opção."
        else:
            return "Não entendi sua solicitação. Envie 'menu' para ver as opções."
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
