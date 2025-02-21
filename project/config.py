import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'minha-chave-secreta')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'minha-chave-jwt')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///db.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Variáveis para integração com Twilio
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'seu_account_sid')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'seu_auth_token')
    TWILIO_NUMBER = os.getenv('TWILIO_NUMBER', '+1234567890')
    
    # Variável para integração com OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sua_api_key')