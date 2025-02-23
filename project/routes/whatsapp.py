from flask import Blueprint, request, jsonify
from models import db, User
from services.twilio_service import send_whatsapp_message # type: ignore
# ou "from .twilio_service import ..."

whatsapp_bp = Blueprint('whatsapp', __name__)

@whatsapp_bp.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    from_number = request.form.get('From')
    body = request.form.get('Body') or ""
    body = body.strip().lower()

    # Buscar user
    user = User.query.filter_by(phone=from_number).first()
    if not user:
        # Criar user ou pedir cadastro
        user = User(phone=from_number, name="New")
        db.session.add(user)
        db.session.commit()
        send_whatsapp_message(from_number, "Olá! Você foi cadastrado automaticamente. Qual seu nome?")
        return jsonify({"status": "new_user_created"})

    # Verificar fluxo ativo
    if user.current_flow == 'checkin':
        return handle_checkin_flow(user, body)

    # Caso não esteja em fluxo, mostrar menu etc.
    if body in ['menu', 'oi', 'olá']:
        menu_text = (
            "Selecione uma opção:\n"
            "1. Registrar consumo\n"
            "2. Consultar metas\n"
            "3. Fazer check-in semanal"
        )
        send_whatsapp_message(from_number, menu_text)
        return jsonify({"status": "menu_displayed"})

    elif body == '1':
        # Ex: registrar consumo
        send_whatsapp_message(from_number, "Quantos ml você consumiu agora?")
        return jsonify({"status": "consumption_prompt"})
    
    elif body == '2':
        # Consultar metas
        # ...
        return jsonify({"status": "goals_listed"})

    elif body == '3':
        # Iniciar check-in
        user.current_flow = 'checkin'
        user.flow_step = 1
        db.session.commit()
        send_whatsapp_message(from_number, "Check-in iniciado! Pergunta 1: Como foi sua alimentação?")
        return jsonify({"status": "checkin_started"})

    else:
        send_whatsapp_message(from_number, "Digite 'menu' para ver as opções.")
        return jsonify({"status": "unrecognized"})
def handle_checkin_flow(user, body):
    from_number = user.phone
    step = user.flow_step

    if step == 1:
        # Salva resposta da pergunta 1
        print(f"Resposta Q1: {body}")
        user.flow_step = 2
        db.session.commit()
        send_whatsapp_message(from_number, "Pergunta 2: Quanto tempo de exercício você fez essa semana?")
        return jsonify({"status": "checkin_step_1_answered"})
    elif step == 2:
        print(f"Resposta Q2: {body}")
        user.flow_step = 3
        db.session.commit()
        send_whatsapp_message(from_number, "Pergunta 3: Alguma dificuldade?")
        return jsonify({"status": "checkin_step_2_answered"})
    elif step == 3:
        print(f"Resposta Q3: {body}")
        user.current_flow = None
        user.flow_step = 0
        db.session.commit()
        send_whatsapp_message(from_number, "Check-in finalizado, obrigado!")
        return jsonify({"status": "checkin_completed"})