"""Monta o relatório: busca dados -> calcula métricas -> pede o texto à IA -> salva em Markdown."""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from config import Settings
from metricas import calcular_metricas
from periodos import calcular_periodos
from prompts import SYSTEM, montar_prompt_usuario


@dataclass
class Relatorio:
    tipo: str
    periodo: str
    metricas: dict
    texto_ia: Optional[str]
    markdown: str
    slug: str  # usado no nome do arquivo, ex.: 2026-11-16_a_2026-11-22


def _brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _tabela(titulo: str, cabecalho: list, linhas: list) -> str:
    if not linhas:
        return f"### {titulo}\n\n_Nenhum item._\n"
    out = [f"### {titulo}", "", "| " + " | ".join(cabecalho) + " |", "|" + "---|" * len(cabecalho)]
    out += ["| " + " | ".join(str(c) for c in linha) + " |" for linha in linhas]
    return "\n".join(out) + "\n"


def renderizar_dados(m: dict) -> str:
    """Tabelas calculadas pelo código (não pela IA), para conferir os números do texto."""
    t, a = m["totais"], m["totais_periodo_anterior"]
    partes = [
        "## Dados do período",
        "",
        _tabela("Totais", ["", "Período", "Anterior"], [
            ["Unidades vendidas", t["unidades_vendidas"], a["unidades_vendidas"]],
            ["Faturamento estimado", _brl(t["faturamento_estimado"]), _brl(a["faturamento_estimado"])],
            ["Lucro bruto estimado", _brl(t["lucro_bruto_estimado"]), _brl(a["lucro_bruto_estimado"])],
        ]),
        _tabela("Mais vendidos", ["Produto", "Categoria", "Unidades", "Faturamento"],
                [[x["produto"], x["categoria"], x["unidades"], _brl(x["faturamento"])] for x in m["mais_vendidos"]]),
        _tabela("Abaixo do estoque mínimo", ["Produto", "Atual", "Mínimo"],
                [[x["produto"], x["estoque_atual"], x["estoque_minimo"]] for x in m["abaixo_do_estoque_minimo"]]),
        _tabela("Sem vendas no período", ["Produto", "Estoque", "Valor parado (custo)"],
                [[x["produto"], x["estoque_atual"], _brl(x["valor_parado_custo"])] for x in m["sem_vendas_no_periodo"]]),
        _tabela("Reposição sugerida", ["Produto", "Estoque", "Dias restantes", "Comprar", "Custo estimado"],
                [[x["produto"], x["estoque_atual"], x["dias_de_estoque_restantes"],
                  x["quantidade_sugerida"], _brl(x["custo_estimado"])] for x in m["reposicao_sugerida"]]),
    ]
    return "\n".join(partes)


def gerar_relatorio(tipo: str, fonte, llm, settings: Settings, referencia: Optional[date] = None) -> Relatorio:
    """`llm` pode ser None: nesse caso só as tabelas de dados são geradas."""
    referencia = referencia or date.today()
    periodo, anterior = calcular_periodos(tipo, referencia)
    metricas = calcular_metricas(
        produtos=fonte.listar_produtos(),
        mov_atual=fonte.listar_movimentacoes(periodo.inicio, periodo.fim),
        mov_anterior=fonte.listar_movimentacoes(anterior.inicio, anterior.fim),
        periodo=periodo, periodo_anterior=anterior,
        dias_cobertura=settings.dias_cobertura, max_itens=settings.max_itens,
    )
    texto = llm.gerar(SYSTEM, montar_prompt_usuario(tipo, metricas)) if llm else None
    cabecalho = f"# Relatório {tipo} de estoque — {periodo.rotulo()}\n"
    markdown = "\n".join([cabecalho, texto or "", "", renderizar_dados(metricas)])
    slug = f"{periodo.inicio.isoformat()}_a_{periodo.fim.isoformat()}"
    return Relatorio(tipo, periodo.rotulo(), metricas, texto, markdown, slug)


def salvar(relatorio: Relatorio, pasta: str) -> Path:
    Path(pasta).mkdir(parents=True, exist_ok=True)
    caminho = Path(pasta) / f"relatorio-{relatorio.tipo}-{relatorio.slug}.md"
    caminho.write_text(relatorio.markdown, encoding="utf-8")
    return caminho
