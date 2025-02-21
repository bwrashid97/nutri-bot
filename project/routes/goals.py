from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from project.models import Goal
from project.extensions import db
from marshmallow import Schema, fields, ValidationError

goals_bp = Blueprint('goals', __name__)

class GoalSchema(Schema):
    tipo = fields.Str(required=True)
    frequencia = fields.Int(required=True)

goal_schema = GoalSchema()

@goals_bp.route('/', methods=['POST'])
@jwt_required()
def create_goal():
    user_id = get_jwt_identity()
    data = request.get_json()
    try:
        valid_data = goal_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 422

    nova_meta = Goal(
        user_id=user_id,
        tipo=valid_data['tipo'],
        frequencia=valid_data['frequencia'],
        concluido=False
    )
    db.session.add(nova_meta)
    db.session.commit()
    return jsonify({"message": "Meta criada", "goal_id": nova_meta.id}), 201

@goals_bp.route('/', methods=['GET'])
@jwt_required()
def get_goals():
    user_id = get_jwt_identity()
    metas = Goal.query.filter_by(user_id=user_id).all()
    resultado = [{
        "id": meta.id,
        "tipo": meta.tipo,
        "frequencia": meta.frequencia,
        "concluido": meta.concluido
    } for meta in metas]
    return jsonify(resultado), 200

@goals_bp.route('/<int:goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    data = request.get_json()
    meta = Goal.query.get(goal_id)
    if not meta:
        return jsonify({"error": "Meta não encontrada"}), 404
    meta.tipo = data.get('tipo', meta.tipo)
    meta.frequencia = data.get('frequencia', meta.frequencia)
    if 'concluido' in data:
        meta.concluido = data.get('concluido')
    db.session.commit()
    return jsonify({"message": "Meta atualizada"}), 200

@goals_bp.route('/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    meta = Goal.query.get(goal_id)
    if not meta:
        return jsonify({"error": "Meta não encontrada"}), 404
    db.session.delete(meta)
    db.session.commit()
    return jsonify({"message": "Meta deletada"}), 200
