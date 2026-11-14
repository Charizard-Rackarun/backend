"""Desafio Sexta 13: toda sexta-feira 13 o sistema libera ofertas secretas e pontos em dobro."""

from datetime import date

from app.services import tempo

MULTIPLICADOR_PONTOS = 2
NOME_EVENTO = "Sexta 13 — Ofertas Secretas"


def eh_sexta_13(d: date) -> bool:
    return d.day == 13 and d.weekday() == 4  # 4 = sexta-feira


def evento_ativo() -> bool:
    return eh_sexta_13(tempo.hoje())


def proxima_sexta_13(a_partir_de: date) -> date:
    """Primeira Sexta 13 em ou depois da data informada."""
    ano, mes = a_partir_de.year, a_partir_de.month
    while True:
        candidata = date(ano, mes, 13)
        if candidata >= a_partir_de and eh_sexta_13(candidata):
            return candidata
        mes += 1
        if mes == 13:
            ano, mes = ano + 1, 1
