from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from project.models import CheckinResponse
from project.extensions import db
from marshmallow import Schema, fields, ValidationError

checkin_bp = Blueprint('checkin', __name__)

class CheckinSchema(Schema):
    pergunta = fields.Str(required=True)
    resposta = fields.Str(required=True)

checkin_schema = CheckinSchema()

@checkin_bp.route('/', methods=['POST'])
@jwt_required()
def create_checkin():
    user_id = get_jwt_identity()
    data = request.get_json()
    try:
        valid_data = checkin_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 422

    novo_checkin = CheckinResponse(
        user_id=user_id,
        pergunta=valid_data['pergunta'],
        resposta=valid_data['resposta']
    )
    db.session.add(novo_checkin)
    db.session.commit()
    return jsonify({"message": "Check-in criado", "checkin_id": novo_checkin.id}), 201

@checkin_bp.route('/', methods=['GET'])
@jwt_required()
def get_checkins():
    user_id = get_jwt_identity()
    checkins = CheckinResponse.query.filter_by(user_id=user_id).all()
    resultado = [{
        "id": checkin.id,
        "data": checkin.data.strftime("%Y-%m-%d %H:%M"),
        "pergunta": checkin.pergunta,
        "resposta": checkin.resposta
    } for checkin in checkins]
    return jsonify(resultado), 200
