"""Cálculo dos números do relatório. Tudo aqui é determinístico (sem IA):
a IA só recebe estes números já prontos e escreve o texto em cima deles."""
import math
from collections import defaultdict
from typing import Dict, List, Optional

from data_source import Movimentacao, Produto
from periodos import Periodo


def _variacao_pct(atual: float, anterior: float) -> Optional[float]:
    if anterior <= 0:
        return None
    return round((atual - anterior) / anterior * 100, 1)


def _saidas_por_produto(movs: List[Movimentacao]) -> Dict[int, int]:
    saidas: Dict[int, int] = defaultdict(int)
    for m in movs:
        if m.tipo == "saida":
            saidas[m.produto_id] += m.quantidade
    return saidas


def _totais(movs: List[Movimentacao], produtos: Dict[int, Produto]) -> dict:
    entradas = sum(m.quantidade for m in movs if m.tipo == "entrada")
    saidas = _saidas_por_produto(movs)
    unidades = sum(saidas.values())
    faturamento = sum(q * produtos[pid].preco_venda for pid, q in saidas.items() if pid in produtos)
    custo = sum(q * produtos[pid].preco_custo for pid, q in saidas.items() if pid in produtos)
    return {
        "unidades_vendidas": unidades,
        "unidades_recebidas": entradas,
        "faturamento_estimado": round(faturamento, 2),
        "lucro_bruto_estimado": round(faturamento - custo, 2),
    }


def calcular_metricas(
    produtos: List[Produto],
    mov_atual: List[Movimentacao],
    mov_anterior: List[Movimentacao],
    periodo: Periodo,
    periodo_anterior: Periodo,
    dias_cobertura: int = 14,
    max_itens: int = 10,
) -> dict:
    por_id = {p.id: p for p in produtos}
    atual = _totais(mov_atual, por_id)
    anterior = _totais(mov_anterior, por_id)
    saidas = _saidas_por_produto(mov_atual)

    comparacao = {
        "unidades_vendidas_pct": _variacao_pct(atual["unidades_vendidas"], anterior["unidades_vendidas"]),
        "faturamento_pct": _variacao_pct(atual["faturamento_estimado"], anterior["faturamento_estimado"]),
        "lucro_bruto_pct": _variacao_pct(atual["lucro_bruto_estimado"], anterior["lucro_bruto_estimado"]),
    }

    top = sorted(saidas.items(), key=lambda kv: kv[1], reverse=True)[:max_itens]
    mais_vendidos = [
        {"produto": por_id[pid].nome, "categoria": por_id[pid].categoria, "unidades": q,
         "faturamento": round(q * por_id[pid].preco_venda, 2)}
        for pid, q in top if pid in por_id
    ]

    fat_categoria: Dict[str, float] = defaultdict(float)
    for pid, q in saidas.items():
        if pid in por_id:
            fat_categoria[por_id[pid].categoria] += q * por_id[pid].preco_venda
    por_categoria = [
        {"categoria": c, "faturamento": round(v, 2)}
        for c, v in sorted(fat_categoria.items(), key=lambda kv: kv[1], reverse=True)
    ]

    abaixo = sorted(
        (p for p in produtos if p.estoque_atual < p.estoque_minimo),
        key=lambda p: p.estoque_minimo - p.estoque_atual, reverse=True,
    )
    abaixo_minimo = [
        {"produto": p.nome, "estoque_atual": p.estoque_atual, "estoque_minimo": p.estoque_minimo}
        for p in abaixo[:max_itens]
    ]

    parados_lista = sorted(
        (p for p in produtos if p.estoque_atual > 0 and saidas.get(p.id, 0) == 0),
        key=lambda p: p.estoque_atual * p.preco_custo, reverse=True,
    )
    parados = [
        {"produto": p.nome, "estoque_atual": p.estoque_atual,
         "valor_parado_custo": round(p.estoque_atual * p.preco_custo, 2)}
        for p in parados_lista[:max_itens]
    ]

    # Sugestão de reposição: repor até cobrir `dias_cobertura` dias no ritmo de venda do período.
    reposicao = []
    for pid, q in saidas.items():
        p = por_id.get(pid)
        if not p:
            continue
        media_diaria = q / periodo.dias
        dias_restantes = p.estoque_atual / media_diaria if media_diaria else math.inf
        if dias_restantes >= dias_cobertura:
            continue
        sugerida = math.ceil(media_diaria * dias_cobertura) - p.estoque_atual
        if sugerida > 0:
            reposicao.append({
                "produto": p.nome, "estoque_atual": p.estoque_atual,
                "venda_media_diaria": round(media_diaria, 1),
                "dias_de_estoque_restantes": round(dias_restantes, 1),
                "quantidade_sugerida": sugerida,
                "custo_estimado": round(sugerida * p.preco_custo, 2),
            })
    reposicao.sort(key=lambda r: r["dias_de_estoque_restantes"])

    return {
        "periodo": periodo.rotulo(),
        "periodo_anterior": periodo_anterior.rotulo(),
        "dias_no_periodo": periodo.dias,
        "dias_de_cobertura_alvo": dias_cobertura,
        "totais": atual,
        "totais_periodo_anterior": anterior,
        "variacao_vs_periodo_anterior": comparacao,
        "mais_vendidos": mais_vendidos,
        "faturamento_por_categoria": por_categoria,
        "abaixo_do_estoque_minimo": abaixo_minimo,
        "sem_vendas_no_periodo": parados,
        "reposicao_sugerida": reposicao[:max_itens],
    }
