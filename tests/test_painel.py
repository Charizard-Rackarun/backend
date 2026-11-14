from tests.helpers import API, criar_lojista


async def test_rotas_do_painel_exigem_login(client):
    for rota in ("/dashboard", "/campaigns"):
        assert (await client.get(f"{API}{rota}")).status_code == 401


async def test_dashboard_vazio_no_formato_do_frontend(client):
    headers = await criar_lojista(client)
    dados = (await client.get(f"{API}/dashboard", headers=headers)).json()
    assert {"revenue", "revenueChange", "averageTicket", "activeConsumers", "salesSeries",
            "categorySeries", "recentActivity"} <= dados.keys()
    assert len(dados["salesSeries"]) == 7


async def test_dashboard_calcula_vendas(client):
    headers = await criar_lojista(client)
    await client.post(f"{API}/vendas", headers=headers, json={
        "data": "2026-11-10", "produto": "Camisa", "categoria": "Moda", "quantidade": 2, "valor_total": "200.00"})
    await client.post(f"{API}/vendas", headers=headers, json={
        "data": "2026-11-11", "produto": "Calça", "categoria": "Moda", "quantidade": 1, "valor_total": "100.00"})
    d = (await client.get(f"{API}/dashboard", headers=headers)).json()
    assert d["revenue"] == 300.0 and d["orders"] == 2 and d["averageTicket"] == 150.0
    assert d["categorySeries"][0]["name"] == "Moda"
    assert d["recentActivity"][0]["type"] == "sale"


async def test_vendas_de_outro_lojista_ficam_isoladas(client):
    a = await criar_lojista(client, "a@teste.com")
    b = await criar_lojista(client, "b@teste.com")
    await client.post(f"{API}/vendas", headers=a, json={
        "data": "2026-11-10", "produto": "X", "quantidade": 1, "valor_total": "50.00"})
    assert (await client.get(f"{API}/dashboard", headers=b)).json()["revenue"] == 0


async def test_campanha_criada_aparece_ativa_no_periodo(client):
    headers = await criar_lojista(client)
    r = await client.post(f"{API}/campaigns", headers=headers, json={
        "nome": "Look de Verão", "tipo": "Cupom", "desconto": "15%",
        "dataInicio": "2026-11-10", "dataFim": "2026-11-20"})
    assert r.status_code == 201
    campanhas = [c for c in (await client.get(f"{API}/campaigns", headers=headers)).json() if c["id"] != "sexta-13"]
    assert campanhas[0]["name"] == "Look de Verão" and campanhas[0]["status"] == "Ativa"
    assert campanhas[0]["startDate"] == "10/11/2026"


async def test_campanha_com_datas_invertidas_retorna_422(client):
    headers = await criar_lojista(client)
    r = await client.post(f"{API}/campaigns", headers=headers, json={
        "nome": "Errada", "tipo": "Cupom", "desconto": "5%", "dataInicio": "2026-11-20", "dataFim": "2026-11-10"})
    assert r.status_code == 422
