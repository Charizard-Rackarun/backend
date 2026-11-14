from tests.helpers import API, criar_lojista, publicar_questionario, respostas


async def test_visitante_responde_ganha_pontos_e_nao_repete(client):
    headers = await criar_lojista(client)
    q = await publicar_questionario(client, headers)
    r = await client.post(f"{API}/public/questionarios/{q['id']}/respostas", json=respostas(q, [0, 1]))
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["pontosGanhos"] == 10 and corpo["pontosTotal"] == 10 and corpo["visitanteToken"]
    token = {"X-Visitante-Token": corpo["visitanteToken"]}
    repetida = await client.post(f"{API}/public/questionarios/{q['id']}/respostas",
                                 json=respostas(q, [0]), headers=token)
    assert repetida.status_code == 409


async def test_resposta_invalida_retorna_422(client):
    headers = await criar_lojista(client)
    q = await publicar_questionario(client, headers)
    r = await client.post(f"{API}/public/questionarios/{q['id']}/respostas",
                          json={"respostas": [{"perguntaId": 999, "opcaoIds": [1]}]})
    assert r.status_code == 422


async def test_questionario_inativo_some_para_o_visitante(client):
    headers = await criar_lojista(client)
    q = await publicar_questionario(client, headers)
    assert (await client.get(f"{API}/public/questionarios/{q['id']}")).status_code == 200
    await client.patch(f"{API}/questionarios/{q['id']}", json={"ativo": False}, headers=headers)
    assert (await client.get(f"{API}/public/questionarios/{q['id']}")).status_code == 404


async def test_resultados_so_para_o_dono_e_com_k_anonimato(client):
    dono = await criar_lojista(client, "dono@teste.com")
    outro = await criar_lojista(client, "outro@teste.com")
    q = await publicar_questionario(client, dono)
    await client.post(f"{API}/public/questionarios/{q['id']}/respostas", json=respostas(q, [0]))
    assert (await client.get(f"{API}/questionarios/{q['id']}/resultados", headers=outro)).status_code == 404
    r = (await client.get(f"{API}/questionarios/{q['id']}/resultados", headers=dono)).json()
    assert r["suprimido"] is True and r["perguntas"][0]["opcoes"][0]["total"] is None  # 1 < mínimo (2)
    await client.post(f"{API}/public/questionarios/{q['id']}/respostas", json=respostas(q, [0, 1]))
    r = (await client.get(f"{API}/questionarios/{q['id']}/resultados", headers=dono)).json()
    assert r["suprimido"] is False and r["perguntas"][0]["opcoes"][0]["total"] == 2
