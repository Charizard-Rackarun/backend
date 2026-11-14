NIVEIS = [(0, "Explorador"), (300, "Caçador de ofertas"), (1000, "Mestre das vitrines")]


def nivel_para(pontos: int) -> tuple[str, int]:
    """Devolve (nome do nível atual, pontos necessários para o próximo nível)."""
    atual, proximo = NIVEIS[0][1], NIVEIS[1][0]
    for i, (minimo, nome) in enumerate(NIVEIS):
        if pontos >= minimo:
            atual = nome
            proximo = NIVEIS[i + 1][0] if i + 1 < len(NIVEIS) else max(pontos, minimo, 1)
    return atual, proximo
