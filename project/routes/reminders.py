from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from project.models import Reminder
from project.extensions import db

reminders_bp = Blueprint('reminders', __name__)

@reminders_bp.route('/', methods=['GET'])
@jwt_required()
def get_reminders():
    user_id = get_jwt_identity()
    reminders = Reminder.query.filter_by(user_id=user_id).all()
    result = [reminder.to_dict() for reminder in reminders]
    return jsonify(result), 200

@reminders_bp.route('/', methods=['POST'])
@jwt_required()
def create_reminder():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data.get('mensagem') or not data.get('intervalo'):
        return jsonify({"error": "Campos 'mensagem' e 'intervalo' são obrigatórios."}), 400
    reminder = Reminder(user_id=user_id, mensagem=data.get('mensagem'), intervalo=data.get('intervalo'))
    db.session.add(reminder)
    db.session.commit()
    return jsonify(reminder.to_dict()), 201

@reminders_bp.route('/<int:reminder_id>', methods=['PUT'])
@jwt_required()
def update_reminder(reminder_id):
    user_id = get_jwt_identity()
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    if not reminder:
        return jsonify({"error": "Lembrete não encontrado."}), 404
    data = request.get_json()
    if 'mensagem' in data:
        reminder.mensagem = data['mensagem']
    if 'intervalo' in data:
        reminder.intervalo = data['intervalo']
    db.session.commit()
    return jsonify(reminder.to_dict()), 200

@reminders_bp.route('/<int:reminder_id>', methods=['DELETE'])
@jwt_required()
def delete_reminder(reminder_id):
    user_id = get_jwt_identity()
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    if not reminder:
        return jsonify({"error": "Lembrete não encontrado."}), 404
    db.session.delete(reminder)
    db.session.commit()
    return jsonify({"message": "Lembrete removido com sucesso."}), 200

