# project/schemas.py
from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3),
        error_messages={
            "required": "O campo 'username' é obrigatório.",
            "validator_failed": "O 'username' deve ter pelo menos 3 caracteres."
        }
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6),
        error_messages={
            "required": "A senha é obrigatória.",
            "validator_failed": "A senha deve ter pelo menos 6 caracteres."
        }
    )


