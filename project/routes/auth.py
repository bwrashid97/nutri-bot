from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta
from marshmallow import Schema, fields, validate, ValidationError
from project.models import User
from project.extensions import db
import bcrypt

auth_bp = Blueprint('auth', __name__)

class UserSchema(Schema):
    nome = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        error_messages={
            "required": "O campo 'nome' é obrigatório.",
            "validator_failed": "O campo 'nome' não pode ser vazio."
        }
    )
    peso = fields.Float(
        required=True,
        error_messages={"required": "O campo 'peso' é obrigatório."}
    )
    altura = fields.Float(
        required=True,
        error_messages={"required": "O campo 'altura' é obrigatório."}
    )
    idade = fields.Int(
        required=True,
        error_messages={"required": "O campo 'idade' é obrigatório."}
    )
    email = fields.Email(
        required=True,
        error_messages={
            "required": "O campo 'email' é obrigatório.",
            "invalid": "Forneça um email válido."
        }
    )
    senha = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=6),
        error_messages={
            "required": "O campo 'senha' é obrigatório.",
            "validator_failed": "A senha deve ter pelo menos 6 caracteres."
        }
    )

user_schema = UserSchema()

@auth_bp.route('/register', methods=['POST'])
def register():
    json_data = request.get_json()
    try:
        data = user_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 422

    # Verifica se o usuário já existe
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"error": "Usuário já cadastrado."}), 400

    # Cria hash da senha
    hashed_pw = bcrypt.hashpw(data.get('senha').encode('utf-8'), bcrypt.gensalt())

    novo_usuario = User(
        nome=data.get('nome'),
        peso=data.get('peso'),
        altura=data.get('altura'),
        idade=data.get('idade'),
        email=data.get('email'),
        senha=hashed_pw.decode('utf-8')
    )
    db.session.add(novo_usuario)
    db.session.commit()
    return jsonify({"message": "Usuário registrado com sucesso!"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    json_data = request.get_json()
    email = json_data.get('email')
    senha = json_data.get('senha')
    usuario = User.query.filter_by(email=email).first()
    if usuario and bcrypt.checkpw(senha.encode('utf-8'), usuario.senha.encode('utf-8')):
        token = create_access_token(identity=usuario.id, expires_delta=timedelta(hours=1))
        return jsonify({"access_token": token}), 200
    return jsonify({"error": "Credenciais inválidas"}), 401
