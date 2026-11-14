from datetime import date

API = "/api/v1"
DIA_COMUM = date(2026, 11, 12)   # quinta-feira
SEXTA_13 = date(2026, 11, 13)    # sexta-feira 13

QUESTIONARIO = {
    "titulo": "O que você procura hoje?",
    "pontos": 10,
    "perguntas": [{
        "texto": "Quais categorias te interessam?", "tipo": "multipla", "dimensao": "categoria",
        "opcoes": [{"texto": "Moda"}, {"texto": "Beleza"}, {"texto": "Alimentação"}],
    }],
}


async def criar_lojista(client, email="loja@teste.com", segmento="Moda", nome="Loja Teste"):
    await client.post(f"{API}/auth/registro", json={
        "nome": nome, "segmento": segmento, "email": email, "senha": "senha-segura-123"})
    r = await client.post(f"{API}/auth/login", data={"username": email, "password": "senha-segura-123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def publicar_questionario(client, headers):
    r = await client.post(f"{API}/questionarios", json=QUESTIONARIO, headers=headers)
    assert r.status_code == 201
    return r.json()


def respostas(questionario, indices):
    pergunta = questionario["perguntas"][0]
    return {"respostas": [{
        "perguntaId": pergunta["id"], "opcaoIds": [pergunta["opcoes"][i]["id"] for i in indices]}]}
