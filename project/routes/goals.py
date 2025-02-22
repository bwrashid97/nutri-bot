from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from project.models import Goal
from project.extensions import db

goals_bp = Blueprint('goals', __name__)

@goals_bp.route('/', methods=['GET'])
@jwt_required()
def get_goals():
    user_id = get_jwt_identity()
    goals = Goal.query.filter_by(user_id=user_id).all()
    result = [goal.to_dict() for goal in goals]
    return jsonify(result), 200

@goals_bp.route('/', methods=['POST'])
@jwt_required()
def create_goal():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data.get('descricao'):
        return jsonify({"error": "Descrição é obrigatória."}), 400
    goal = Goal(user_id=user_id, descricao=data.get('descricao'), meta_semana=data.get('meta_semana'))
    db.session.add(goal)
    db.session.commit()
    return jsonify(goal.to_dict()), 201

@goals_bp.route('/<int:goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    user_id = get_jwt_identity()
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return jsonify({"error": "Meta não encontrada."}), 404
    data = request.get_json()
    if 'descricao' in data:
        goal.descricao = data['descricao']
    if 'meta_semana' in data:
        goal.meta_semana = data['meta_semana']
    db.session.commit()
    return jsonify(goal.to_dict()), 200

@goals_bp.route('/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    user_id = get_jwt_identity()
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return jsonify({"error": "Meta não encontrada."}), 404
    db.session.delete(goal)
    db.session.commit()
    return jsonify({"message": "Meta removida com sucesso."}), 200
