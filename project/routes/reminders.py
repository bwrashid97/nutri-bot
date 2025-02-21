from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from project.models import Reminder
from project.extensions import db
import datetime
from marshmallow import Schema, fields, ValidationError

reminders_bp = Blueprint('reminders', __name__)

class ReminderSchema(Schema):
    texto = fields.Str(required=True)
    horario = fields.Str(required=True)  # Envie no formato "HH:MM"
    repeticao = fields.Str(required=False, load_default="diario")

reminder_schema = ReminderSchema()

@reminders_bp.route('/', methods=['POST'])
@jwt_required()
def create_reminder():
    user_id = get_jwt_identity()
    data = request.get_json()
    try:
        valid_data = reminder_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 422

    # Converte o horário de string para time
    try:
        horario = datetime.datetime.strptime(valid_data['horario'], "%H:%M").time()
    except Exception as e:
        return jsonify({"error": "Formato de horário inválido. Use HH:MM"}), 422

    novo_lembrete = Reminder(
        user_id=user_id,
        texto=valid_data['texto'],
        horario=horario,
        repeticao=valid_data.get('repeticao', 'diario')
    )
    db.session.add(novo_lembrete)
    db.session.commit()
    return jsonify({"message": "Lembrete criado", "reminder_id": novo_lembrete.id}), 201

@reminders_bp.route('/', methods=['GET'])
@jwt_required()
def get_reminders():
    user_id = get_jwt_identity()
    lembretes = Reminder.query.filter_by(user_id=user_id).all()
    resultado = [{
        "id": lembrete.id,
        "texto": lembrete.texto,
        "horario": lembrete.horario.strftime("%H:%M"),
        "repeticao": lembrete.repeticao
    } for lembrete in lembretes]
    return jsonify(resultado), 200
