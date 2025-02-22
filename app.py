import openai
from project.config import Config
from twilio.rest import Client  # Import para integração real (usado se MOCK_INTEGRATIONS=False)

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
    Função para enviar mensagens interativas. No modo mock, apenas imprime.
    Para a integração real, formata a mensagem conforme a API do WhatsApp/Twilio.
    """
    if Config.MOCK_INTEGRATIONS:
        print(f"[MOCK] Enviando para {to}: {text}")
        return "fake_interactive_sid"
    client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
    # Exemplo simples: enviando mensagem de texto.
    # Para mensagens interativas, será necessário seguir o JSON conforme a doc da Twilio.
    message = client.messages.create(
        from_=Config.TWILIO_WHATSAPP_NUMBER,
        to=to,
        body=text
    )
    return message.sid
from flask import Flask, request, jsonify
from project.config import Config
from project.extensions import db
from project.models import User
from datetime import datetime

# Import dos blueprints e funções de integração já feitos anteriormente

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    from flask_migrate import Migrate
    Migrate(app, db)
    from flask_jwt_extended import JWTManager
    JWTManager(app)

    # Registro dos blueprints para endpoints REST (para integração via API, se necessário)
    from project.routes.auth import auth_bp
    from project.routes.goals import goals_bp
    from project.routes.reminders import reminders_bp
    from project.routes.checkin import checkin_bp

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
        from_number = request.form.get('From')  # Ex: 'whatsapp:+551199999999'
        body = request.form.get('Body')           # Texto digitado ou ID do botão

        # Exemplo de diferenciação: se a mensagem vem do admin, pode ser um fluxo administrativo
        admin_number = "whatsapp:+5511999999999"  # Número definido para admin
        if from_number == admin_number:
            response_text = process_admin_message(body, from_number)
        else:
            response_text = process_user_message(body, from_number)

        send_interactive_message(from_number, response_text)
        return "OK", 200

    def process_admin_message(body, from_number):
        # Exemplo simples de fluxo admin
        if body.strip().lower() in ["1", "usuarios"]:
            users = User.query.all()
            msg = "Lista de Usuários:\n"
            for u in users:
                days_left = (u.access_expiration - datetime.utcnow()).days
                msg += f"{u.nome} ({u.email}): {days_left} dias restantes\n"
            return msg
        elif body.strip().lower() in ["2", "reativar"]:
            return "Por favor, informe o email do usuário a reativar."
        # Outras opções administrativas
        else:
            return "Opção inválida. Por favor, escolha: 1) Usuários 2) Reativar."

    def process_user_message(body, from_number):
        # Exemplo de fluxo para alunos
        if body.strip() in ["+500ml", "add_500"]:
            # Aqui você atualizaria o consumo de água do usuário
            # Exemplo: atualizar no modelo WaterConsumption (não implementado detalhadamente aqui)
            return "Você adicionou 500ml ao seu consumo hoje. Continue assim!"
        elif body.strip() in ["+1000ml", "add_1000"]:
            return "Você adicionou 1000ml ao seu consumo hoje. Continue assim!"
        elif body.strip().lower() in ["menu", "início"]:
            # Retorna um menu interativo básico
            return ("Olá! Escolha uma opção:\n"
                    "1. Registrar consumo de água\n"
                    "2. Definir/Editar metas\n"
                    "3. Realizar check-in semanal\n"
                    "4. Consultar dicas (ex.: treino)\n"
                    "Envie o número correspondente ou clique no botão adequado.")
        else:
            return "Não entendi sua solicitação. Por favor, envie 'menu' para ver as opções."

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
