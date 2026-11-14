from tests.helpers import API, criar_lojista, publicar_questionario, respostas

CUPOM = {"titulo": "Look novo", "descricao": "Acima de R$ 120", "desconto": "15% OFF",
         "categoria": "Moda", "custoPontos": 10, "estoque": 1, "validade": "2026-12-31"}


async def test_carteira_mostra_saldo_do_visitante(client):
    loja = await criar_lojista(client)
    q = await publicar_questionario(client, loja)
    await client.post(f"{API}/cupons", headers=loja, json=CUPOM)
    sem_token = (await client.get(f"{API}/rewards")).json()
    assert sem_token["points"] == 0 and len(sem_token["coupons"]) == 1
    v = (await client.post(f"{API}/public/questionarios/{q['id']}/respostas", json=respostas(q, [0]))).json()
    com_token = (await client.get(f"{API}/rewards", headers={"X-Visitante-Token": v["visitanteToken"]})).json()
    assert com_token["points"] == 10 and com_token["level"] == "Explorador"
    assert com_token["coupons"][0]["store"] == "Loja Teste"


async def test_resgate_e_validacao_no_balcao(client):
    loja = await criar_lojista(client)
    q = await publicar_questionario(client, loja)
    cupom = (await client.post(f"{API}/cupons", headers=loja, json=CUPOM)).json()
    v = (await client.post(f"{API}/public/questionarios/{q['id']}/respostas", json=respostas(q, [0]))).json()
    token = {"X-Visitante-Token": v["visitanteToken"]}

    resgate = await client.post(f"{API}/coupons/redeem", json={"code": cupom["codigo"]}, headers=token)
    assert resgate.status_code == 200 and resgate.json()["pontosRestantes"] == 0
    codigo = resgate.json()["resgateCodigo"]
    # o estoque (1) acabou
    assert (await client.post(f"{API}/coupons/redeem", json={"code": cupom["codigo"]}, headers=token)).status_code == 409

    assert (await client.post(f"{API}/resgates/validar", json={"codigo": codigo}, headers=loja)).status_code == 200
    assert (await client.post(f"{API}/resgates/validar", json={"codigo": codigo}, headers=loja)).status_code == 409


async def test_lojista_so_valida_resgates_dos_proprios_cupons(client):
    loja = await criar_lojista(client)
    outra = await criar_lojista(client, "outra@teste.com")
    q = await publicar_questionario(client, loja)
    cupom = (await client.post(f"{API}/cupons", headers=loja, json=CUPOM)).json()
    v = (await client.post(f"{API}/public/questionarios/{q['id']}/respostas", json=respostas(q, [0]))).json()
    codigo = (await client.post(f"{API}/coupons/redeem", json={"code": cupom["codigo"]},
                                headers={"X-Visitante-Token": v["visitanteToken"]})).json()["resgateCodigo"]
    assert (await client.post(f"{API}/resgates/validar", json={"codigo": codigo}, headers=outra)).status_code == 404


async def test_resgate_sem_pontos_ou_sem_token(client):
    loja = await criar_lojista(client)
    cupom = (await client.post(f"{API}/cupons", headers=loja, json={**CUPOM, "custoPontos": 50})).json()
    assert (await client.post(f"{API}/coupons/redeem", json={"code": cupom["codigo"]})).status_code == 401
    q = await publicar_questionario(client, loja)
    v = (await client.post(f"{API}/public/questionarios/{q['id']}/respostas", json=respostas(q, [0]))).json()
    r = await client.post(f"{API}/coupons/redeem", json={"code": cupom["codigo"]},
                          headers={"X-Visitante-Token": v["visitanteToken"]})
    assert r.status_code == 400
