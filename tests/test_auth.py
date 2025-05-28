# tests/test_auth.py
import json

def test_register(test_client):
    data = {
        "nome": "Teste",
        "peso": 70.0,
        "altura": 1.75,
        "idade": 30,
        "email": "teste@exemplo.com",
        "senha": "123456"
    }
    response = test_client.post('/auth/register', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    json_response = response.get_json()
    assert "Usuário registrado com sucesso!" in json_response["message"]
