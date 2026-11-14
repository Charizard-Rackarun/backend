from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentEstabelecimento, DbSession, VisitanteOpcional
from app.core.config import settings
from app.core.security import generate_token, hash_token
from app.models import (
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
    QuestionarioRead,
    QuestionarioResumo,
    QuestionarioStatus,
    RespostaCreate,
    RespostaResultado,
    ResultadosQuestionario,
)

router = APIRouter(prefix="/questionarios", tags=["Questionários (lojista)"])
public_router = APIRouter(prefix="/public/questionarios", tags=["Questionários (visitante)"])


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
                opcoes=[Opcao(texto=o.texto, ordem=j) for j, o in enumerate(p.opcoes)],
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


@router.get("/{questionario_id}/resultados", response_model=ResultadosQuestionario)
async def resultados(questionario_id: int, estabelecimento: CurrentEstabelecimento, db: DbSession):
    q = await _do_dono(db, questionario_id, estabelecimento.id)
    total = await db.scalar(select(func.count(Resposta.id)).where(Resposta.questionario_id == q.id)) or 0
    suprimido = total < settings.min_group_size  # poucas respostas: não exibe contagens (LGPD)
    contagens = dict((await db.execute(
        select(RespostaItem.opcao_id, func.count(RespostaItem.id))
        .join(Resposta, Resposta.id == RespostaItem.resposta_id)
        .where(Resposta.questionario_id == q.id)
        .group_by(RespostaItem.opcao_id)
    )).all())
    perguntas = [
        PerguntaResultado(
            pergunta_id=p.id, texto=p.texto,
            opcoes=[
                OpcaoResultado(
                    opcao_id=o.id, texto=o.texto,
                    total=None if suprimido else contagens.get(o.id, 0),
                    percentual=None if suprimido else round(contagens.get(o.id, 0) / total * 100, 1),
                )
                for o in p.opcoes
            ],
        )
        for p in q.perguntas
    ]
    return ResultadosQuestionario(
        questionario_id=q.id, total_respostas=total, suprimido=suprimido, perguntas=perguntas
    )


# ----------------------------- visitante (público) -----------------------------
@public_router.get("/{questionario_id}", response_model=QuestionarioRead)
async def ver_publico(questionario_id: int, db: DbSession):
    q = await db.get(Questionario, questionario_id)
    if q is None or not q.ativo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questionário não encontrado")
    return q


def _validar_respostas(q: Questionario, dados: RespostaCreate) -> None:
    perguntas = {p.id: p for p in q.perguntas}
    respondidas: set[int] = set()
    for r in dados.respostas:
        pergunta = perguntas.get(r.pergunta_id)
        if pergunta is None or r.pergunta_id in respondidas:
            raise HTTPException(422, "Pergunta inválida ou repetida")
        escolhidas = set(r.opcao_ids)
        validas = {o.id for o in pergunta.opcoes}
        if not escolhidas <= validas or (pergunta.tipo == "unica" and len(escolhidas) != 1):
            raise HTTPException(422, "Opção inválida para a pergunta")
        respondidas.add(pergunta.id)
    if respondidas != set(perguntas):
        raise HTTPException(422, "Responda todas as perguntas")


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

    bonus = False  # pontos em dobro na Sexta 13 entram na branch feat/backend-sexta-13
    ganhos = q.pontos
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
