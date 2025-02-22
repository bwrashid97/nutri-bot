import os
import openai
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from project.config import Config
from project.extensions import db
from twilio.rest import Client

# Blueprints REST (para testes via API)
from project.routes.auth import auth_bp
from project.routes.goals import goals_bp
from project.routes.reminders import reminders_bp
from project.routes.checkin import checkin_bp

# Models
from project.models import User, WaterConsumption

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
        print(f"[MOCK SMS] Para: {to} - Mensagem: {message}")
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
    Envia ou simula envio de mensagem (com ou sem botões).
    Para mensagens interativas reais, formatar JSON conforme doc do WhatsApp/Twilio.
    """
    if Config.MOCK_INTEGRATIONS:
        print(f"[MOCK Interactive] Para {to}: {text}")
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

    @app.route('/webhook/whatsapp', methods=['POST'])
    def whatsapp_webhook():
        from_number = request.form.get('From')  # 'whatsapp:+551199999999'
        body = request.form.get('Body')         # Texto digitado ou ID do botão
        lower_body = body.strip().lower() if body else ""

        admin_number = "whatsapp:+5511999999999"  # Ajuste para o número admin real
        if from_number == admin_number:
            response_text = process_admin_message(lower_body, from_number)
        else:
            response_text = process_user_message(lower_body, from_number)

        send_interactive_message(from_number, response_text)
        return "OK", 200

    def process_admin_message(body, from_number):
        if body in ["1", "usuarios"]:
            users = User.query.all()
            msg = "Lista de Usuários:\n"
            for u in users:
                days_left = (u.access_expiration - datetime.utcnow()).days
                msg += f"{u.nome} ({u.email}): {days_left} dias restantes\n"
            msg += "\n[2] Reativar usuário\nEnvie o número correspondente."
            return msg

        elif body in ["2", "reativar"]:
            # Transição de estado simples: peça o email do usuário
            return "Por favor, informe o email do usuário que deseja reativar."

        else:
            # Se for um email, tente reativar
            user = User.query.filter_by(email=body).first()
            if user:
                user.access_expiration = datetime.utcnow() + timedelta(days=30)
                db.session.commit()
                return f"O acesso de {user.nome} foi reativado por mais 30 dias!"
            else:
                return ("Olá, admin! Escolha uma opção:\n"
                        "1. Ver usuários\n"
                        "2. Reativar usuário\n"
                        "Envie o número ou email de um usuário para reativar.")

    def process_user_message(body, from_number):
        # Fluxo para usuários normais
        if body in ["+500ml", "add_500"]:
            return registrar_consumo_agua(from_number, 500)
        elif body in ["+1000ml", "add_1000"]:
            return registrar_consumo_agua(from_number, 1000)
        elif body in ["menu", "início"]:
            return ("Olá! Escolha uma opção:\n"
                    "1. Registrar consumo de água\n"
                    "2. Definir/Editar metas\n"
                    "3. Realizar check-in semanal\n"
                    "4. Consultar dicas de treino/dieta\n"
                    "[cancel] ou [voltar] para sair.")
        elif body in ["cancel", "voltar", "refazer"]:
            return "Voltando ao menu principal. Digite 'menu' para ver as opções."
        elif body in ["1"]:
            # Exemplo simples: responde com botões
            return ("Para registrar água, use +500ml ou +1000ml.\n"
                    "Ou envie 'menu' para voltar.")
        elif body in ["3"]:
            # Exemplo de check-in
            return iniciar_checkin(from_number)
        else:
            return "Não entendi sua solicitação. Envie 'menu' para ver as opções."

    def registrar_consumo_agua(from_number, ml_adicionais):
        # Encontre o user no BD por telefone (opcionalmente)
        user = User.query.filter_by(telefone=from_number).first()
        if not user:
            # Se não encontrar, fallback
            return "Usuário não cadastrado com este número. Envie 'menu' para voltar."

        # Registrar ou atualizar WaterConsumption
        hoje = date.today()
        cons = WaterConsumption.query.filter_by(user_id=user.id, data=hoje).first()
        if not cons:
            cons = WaterConsumption(user_id=user.id, data=hoje, quantidade=0)
            db.session.add(cons)
        cons.quantidade += ml_adicionais
        db.session.commit()

        # Opcional: se quiser meta de água, use Goal ou outro campo
        return f"Você adicionou {ml_adicionais}ml hoje. Total de {cons.quantidade}ml para o dia!"

    def iniciar_checkin(from_number):
        # Poderíamos criar perguntas específicas e armazenar estado
        # Por ora, apenas exemplo:
        return ("Check-in semanal iniciado! Responda às perguntas:\n"
                "1. Quantos dias seguiu a dieta?\n"
                "2. Quantos dias treinou?\n"
                "Envie as respostas em sequência ou 'menu' para voltar.")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
