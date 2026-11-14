from tests.helpers import API, criar_lojista


async def test_login_e_perfil_do_lojista(client):
    headers = await criar_lojista(client)
    me = (await client.get(f"{API}/auth/me", headers=headers)).json()
    assert me["email"] == "loja@teste.com" and me["segmento"] == "Moda"


async def test_login_com_senha_errada_retorna_401(client):
    await criar_lojista(client)
    r = await client.post(f"{API}/auth/login", data={"username": "loja@teste.com", "password": "errada-123"})
    assert r.status_code == 401


async def test_venda_exige_login_e_aceita_categoria(client):
    corpo = {"data": "2026-11-10", "produto": "Camisa", "categoria": "Moda", "quantidade": 2,
             "valor_total": "200.00"}
    assert (await client.post(f"{API}/vendas", json=corpo)).status_code == 401
    headers = await criar_lojista(client)
    r = await client.post(f"{API}/vendas", json=corpo, headers=headers)
    assert r.status_code == 201 and r.json()["categoria"] == "Moda"
