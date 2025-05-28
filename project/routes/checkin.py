from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from project.models import Checkin
from project.extensions import db

checkin_bp = Blueprint('checkin', __name__)

@checkin_bp.route('/', methods=['GET'])
@jwt_required()
def get_checkins():
    user_id = get_jwt_identity()
    checkins = Checkin.query.filter_by(user_id=user_id).all()
    result = [checkin.to_dict() for checkin in checkins]
    return jsonify(result), 200

@checkin_bp.route('/', methods=['POST'])
@jwt_required()
def create_checkin():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data.get('respostas'):
        return jsonify({"error": "As respostas são obrigatórias."}), 400
    checkin = Checkin(user_id=user_id, respostas=data.get('respostas'))
    db.session.add(checkin)
    db.session.commit()
    # Aqui, se desejado, chame a função de IA para gerar dicas
    return jsonify(checkin.to_dict()), 201

