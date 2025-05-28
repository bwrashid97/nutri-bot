from flask import Blueprint, request, jsonify
from project.config import Config
import openai

ia_bp = Blueprint('ia', __name__)

@ia_bp.route('/personalized-plan', methods=['POST'])
def personalized_plan():
    data = request.get_json()
    imc = data.get('imc')  # calcular IMC previamente
    preferencia = data.get('preferencia', 'casa')  # treino em casa ou academia
    prompt = f"Crie um plano de treino para um usuário com IMC {imc} que prefere treinar {preferencia}."
    
    openai.api_key = Config.OPENAI_API_KEY
    response = openai.Completion.create(
        engine="text-davinci-003",  
        prompt=prompt,
        max_tokens=150,
        temperature=0.7
    )
    return jsonify({"plan": response.choices[0].text.strip()}), 200
