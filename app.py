import os
from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from project.config import Config
from project.extensions import db

# Importando blueprints
from project.routes.auth import auth_bp
from project.routes.goals import goals_bp
from project.routes.reminders import reminders_bp
from project.routes.checkin import checkin_bp

# Função para enviar SMS via Twilio (ainda não configurado)
def send_sms(to, message):
    if not all([Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN, Config.TWILIO_NUMBER]):
        raise Exception("Twilio não configurado.")
    from twilio.rest import Client  # type: ignore
    client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
    sms = client.messages.create(
        body=message,
        from_=Config.TWILIO_NUMBER,
        to=to
    )
    return sms.sid

# Função para obter dicas via IA (exemplo com OpenAI)
def get_training_tip(prompt):
    import openai  # type: ignore
    openai.api_key = Config.OPENAI_API_KEY
    response = openai.Completion.create(
         engine="davinci",
         prompt=prompt,
         max_tokens=50
    )
    return response.choices[0].text.strip()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa as extensões
    db.init_app(app)
    migrate = Migrate(app, db)
    JWTManager(app)

    # Registra os blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(goals_bp, url_prefix='/goals')
    app.register_blueprint(reminders_bp, url_prefix='/reminders')
    app.register_blueprint(checkin_bp, url_prefix='/checkin')

    @app.route('/')
    def index():
        return "Servidor Flask rodando!"

    # Endpoint para envio de SMS (integração com Twilio)
    @app.route('/send-sms', methods=['POST'])
    def send_sms_route():
        data = request.get_json()
        to = data.get('to')
        message = data.get('message')
        try:
            sms_sid = send_sms(to, message)
            return jsonify({"message": "SMS enviado", "sms_sid": sms_sid}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Endpoint para obter uma dica via IA
    @app.route('/tip', methods=['POST'])
    def tip():
        data = request.get_json()
        prompt = data.get('prompt')
        try:
            tip_text = get_training_tip(prompt)
            return jsonify({"tip": tip_text}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Rota para painel administrativo (exemplo simples com Jinja2)
    from project.models import User
    @app.route('/admin')
    def admin_panel():
        users = User.query.all()
        return render_template('admin_home.html', users=users)

    # Cria as tabelas dentro do contexto da aplicação
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
