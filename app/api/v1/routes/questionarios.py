from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentEstabelecimento, DbSession, VisitanteOpcional
from app.core.config import settings
from app.core.security import generate_token, hash_token
from app.models import (
    Estabelecimento,
    Opcao,
    Pergunta,
    Questionario,
    Resposta,
    RespostaItem,
    Visitante,
)
from app.schemas.questionario import (
    OpcaoResultado,
    PerguntaResultado,
    QuestionarioCreate,
    QuestionarioPublico,
    QuestionarioPublicoResumo,
    QuestionarioRead,
    QuestionarioResumo,
    QuestionarioStatus,
    RespostaCreate,
    RespostaResultado,
    ResultadosQuestionario,
)
from app.services import sexta13

router = APIRouter(prefix="/questionarios", tags=["Questionários (lojista)"])
public_router = APIRouter(prefix="/public/questionarios", tags=["Questionários (visitante)"])

SEGUNDOS_POR_PERGUNTA = 15


async def _do_dono(db, questionario_id: int, estabelecimento_id: int) -> Questionario:
    q = await db.get(Questionario, questionario_id)
    if q is None or q.estabelecimento_id != estabelecimento_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questionário não encontrado")
    return q


# ----------------------------- lojista -----------------------------
@router.post("", response_model=QuestionarioRead, status_code=status.HTTP_201_CREATED)
async def criar(dados: QuestionarioCreate, estabelecimento: CurrentEstabelecimento, db: DbSession):
    questionario = Questionario(
        estabelecimento_id=estabelecimento.id,
        titulo=dados.titulo,
        descricao=dados.descricao,
        pontos=dados.pontos,
        perguntas=[
            Pergunta(
                texto=p.texto, tipo=p.tipo, dimensao=p.dimensao, ordem=i,
                obrigatoria=p.obrigatoria, max_selecoes=p.max_selecoes,
                opcoes=[Opcao(texto=o.texto, exclusiva=o.exclusiva, ordem=j) for j, o in enumerate(p.opcoes)],
            )
            for i, p in enumerate(dados.perguntas)
        ],
    )
    db.add(questionario)
    await db.commit()
    return questionario


@router.get("", response_model=list[QuestionarioResumo])
async def listar(estabelecimento: CurrentEstabelecimento, db: DbSession):
    consulta = (
        select(Questionario, func.count(Resposta.id))
        .outerjoin(Resposta, Resposta.questionario_id == Questionario.id)
        .where(Questionario.estabelecimento_id == estabelecimento.id)
        .group_by(Questionario.id)
        .order_by(Questionario.id.desc())
    )
    return [
        QuestionarioResumo(id=q.id, titulo=q.titulo, ativo=q.ativo, pontos=q.pontos, total_respostas=n)
        for q, n in (await db.execute(consulta)).all()
    ]


@router.patch("/{questionario_id}", response_model=QuestionarioStatus)
async def alterar_status(
    questionario_id: int, dados: QuestionarioStatus, estabelecimento: CurrentEstabelecimento, db: DbSession
):
    q = await _do_dono(db, questionario_id, estabelecimento.id)
    q.ativo = dados.ativo
    await db.commit()
    return QuestionarioStatus(ativo=q.ativo)


def _resultado_pergunta(p: Pergunta, contagens: dict[int, int], respondentes: int) -> PerguntaResultado:
    opcoes = [
        OpcaoResultado(
            opcao_id=o.id,
            texto=o.texto,
            total=contagens.get(o.id, 0),
            percentual=round(contagens.get(o.id, 0) / respondentes * 100, 1) if respondentes else 0.0,
        )
        for o in p.opcoes
    ]
    media = None
    if p.tipo == "escala" and respondentes:
        # a opção de ordem 0 vale 1, a de ordem 1 vale 2, e assim por diante
        soma = sum((i + 1) * contagens.get(o.id, 0) for i, o in enumerate(p.opcoes))
        media = round(soma / respondentes, 2)
    if p.tipo in ("unica", "multipla"):
        opcoes.sort(key=lambda o: o.total, reverse=True)  # mais escolhidas primeiro (empates mantêm a ordem)
    return PerguntaResultado(
        pergunta_id=p.id, texto=p.texto, tipo=p.tipo, respondentes=respondentes, media=media, opcoes=opcoes
    )


@router.get("/{questionario_id}/resultados", response_model=ResultadosQuestionario)
async def resultados(questionario_id: int, estabelecimento: CurrentEstabelecimento, db: DbSession):
    """Resultados agregados do próprio lojista. As respostas são anônimas (sem nome, e-mail ou telefone),
    então os números sempre aparecem; com poucas respostas vem apenas o aviso de amostra pequena."""
    q = await _do_dono(db, questionario_id, estabelecimento.id)
    total = await db.scalar(select(func.count(Resposta.id)).where(Resposta.questionario_id == q.id)) or 0
    contagens = dict((await db.execute(
        select(RespostaItem.opcao_id, func.count(RespostaItem.id))
        .join(Resposta, Resposta.id == RespostaItem.resposta_id)
        .where(Resposta.questionario_id == q.id)
        .group_by(RespostaItem.opcao_id)
    )).all())
    respondentes = dict((await db.execute(
        select(RespostaItem.pergunta_id, func.count(func.distinct(RespostaItem.resposta_id)))
        .join(Resposta, Resposta.id == RespostaItem.resposta_id)
        .where(Resposta.questionario_id == q.id)
        .group_by(RespostaItem.pergunta_id)
    )).all())
    return ResultadosQuestionario(
        questionario_id=q.id,
        total_respostas=total,
        amostra_pequena=total < settings.min_group_size,
        minimo_recomendado=settings.min_group_size,
        perguntas=[_resultado_pergunta(p, contagens, respondentes.get(p.id, 0)) for p in q.perguntas],
    )


# ----------------------------- visitante (público) -----------------------------
@public_router.get("", response_model=list[QuestionarioPublicoResumo])
async def listar_publicos(db: DbSession, visitante: VisitanteOpcional):
    """Pesquisas ativas de todas as lojas parceiras, para o visitante ganhar mais pontos."""
    linhas = (await db.execute(
        select(Questionario, Estabelecimento.nome, Estabelecimento.segmento)
        .join(Estabelecimento, Estabelecimento.id == Questionario.estabelecimento_id)
        .where(Questionario.ativo.is_(True))
        .order_by(Questionario.id.desc())
        .limit(50)
    )).all()
    respondidos: set[int] = set()
    if visitante is not None:
        respondidos = set((await db.scalars(
            select(Resposta.questionario_id).where(Resposta.visitante_id == visitante.id)
        )).all())
    multiplicador = sexta13.MULTIPLICADOR_PONTOS if sexta13.evento_ativo() else 1
    return [
        QuestionarioPublicoResumo(
            id=q.id, titulo=q.titulo, descricao=q.descricao, loja=loja, segmento=segmento,
            pontos=q.pontos, pontos_hoje=q.pontos * multiplicador,
            total_perguntas=len(q.perguntas), segundos_estimados=len(q.perguntas) * SEGUNDOS_POR_PERGUNTA,
            respondido=q.id in respondidos,
        )
        for q, loja, segmento in linhas
    ]


@public_router.get("/{questionario_id}", response_model=QuestionarioPublico)
async def ver_publico(questionario_id: int, db: DbSession):
    q = await db.get(Questionario, questionario_id)
    if q is None or not q.ativo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questionário não encontrado")
    loja = await db.scalar(select(Estabelecimento.nome).where(Estabelecimento.id == q.estabelecimento_id))
    return QuestionarioPublico.model_validate(q).model_copy(update={"loja": loja or ""})


def _validar_respostas(q: Questionario, dados: RespostaCreate) -> None:
    perguntas = {p.id: p for p in q.perguntas}
    respondidas: set[int] = set()
    for r in dados.respostas:
        pergunta = perguntas.get(r.pergunta_id)
        if pergunta is None or r.pergunta_id in respondidas:
            raise HTTPException(422, "Pergunta inválida ou repetida")
        opcoes = {o.id: o for o in pergunta.opcoes}
        ids = r.opcao_ids
        if len(set(ids)) != len(ids) or not set(ids) <= set(opcoes):
            raise HTTPException(422, "Opção inválida para a pergunta")
        if pergunta.tipo != "multipla":
            if len(ids) != 1:
                raise HTTPException(422, "Escolha apenas uma opção")
        else:
            marcadas = [opcoes[i] for i in ids]
            if len(marcadas) > 1 and any(o.exclusiva for o in marcadas):
                raise HTTPException(422, "A opção exclusiva não pode ser combinada com outras")
            if pergunta.max_selecoes and len(marcadas) > pergunta.max_selecoes:
                raise HTTPException(422, f"Escolha no máximo {pergunta.max_selecoes} opções")
        respondidas.add(pergunta.id)
    if {p.id for p in q.perguntas if p.obrigatoria} - respondidas:
        raise HTTPException(422, "Responda todas as perguntas obrigatórias")


@public_router.post(
    "/{questionario_id}/respostas", response_model=RespostaResultado, status_code=status.HTTP_201_CREATED
)
async def responder(
    questionario_id: int, dados: RespostaCreate, db: DbSession, visitante: VisitanteOpcional
):
    q = await db.get(Questionario, questionario_id)
    if q is None or not q.ativo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questionário não encontrado")
    _validar_respostas(q, dados)

    token = None
    if visitante is None:
        token = generate_token()
        visitante = Visitante(token_hash=hash_token(token), pontos=0)
        db.add(visitante)
        await db.flush()
    elif await db.scalar(
        select(Resposta.id).where(Resposta.questionario_id == q.id, Resposta.visitante_id == visitante.id)
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "Você já respondeu este questionário")

    resposta = Resposta(questionario_id=q.id, visitante_id=visitante.id)
    db.add(resposta)
    await db.flush()
    db.add_all(
        RespostaItem(resposta_id=resposta.id, pergunta_id=r.pergunta_id, opcao_id=opcao_id)
        for r in dados.respostas for opcao_id in r.opcao_ids
    )

    bonus = sexta13.evento_ativo()
    ganhos = q.pontos * (sexta13.MULTIPLICADOR_PONTOS if bonus else 1)
    await db.execute(
        update(Visitante).where(Visitante.id == visitante.id).values(pontos=Visitante.pontos + ganhos)
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Você já respondeu este questionário")
    await db.refresh(visitante)
    return RespostaResultado(
        pontos_ganhos=ganhos, pontos_total=visitante.pontos, bonus_sexta_13=bonus, visitante_token=token
    )
