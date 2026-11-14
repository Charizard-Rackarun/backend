from tests.helpers import API, criar_lojista, publicar_questionario, respostas


async def test_rotas_de_insights_exigem_login(client):
    for rota in ("/consumers/segments", "/opportunities"):
        assert (await client.get(f"{API}{rota}")).status_code == 401


async def test_oportunidades_geradas_a_partir_das_respostas(client):
    headers = await criar_lojista(client)
    await criar_lojista(client, "aura@teste.com", segmento="Beleza", nome="Perfumaria Aura")
    q = await publicar_questionario(client, headers)
    for indices in ([0, 1], [0, 1], [0, 1], [2], [2]):
        await client.post(f"{API}/public/questionarios/{q['id']}/respostas", json=respostas(q, indices))
    ops = (await client.post(f"{API}/opportunities/gerar", headers=headers)).json()
    assert ops and ops[0]["title"] in ("Moda + Beleza", "Beleza + Moda")
    assert ops[0]["confidence"] == 100 and ops[0]["stores"] == ["Perfumaria Aura"]
    assert (await client.get(f"{API}/opportunities", headers=headers)).json()[0]["id"] == ops[0]["id"]
    segmentos = (await client.get(f"{API}/consumers/segments", headers=headers)).json()
    assert {s["name"] for s in segmentos} >= {"Moda", "Beleza"}


async def test_poucas_respostas_nao_geram_segmentos(client):
    headers = await criar_lojista(client)
    q = await publicar_questionario(client, headers)
    await client.post(f"{API}/public/questionarios/{q['id']}/respostas", json=respostas(q, [0]))
    assert (await client.get(f"{API}/consumers/segments", headers=headers)).json() == []  # 1 < mínimo (2)
