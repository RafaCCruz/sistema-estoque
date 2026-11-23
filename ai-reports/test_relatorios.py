from datetime import date

from config import Settings
from data_source import Movimentacao, Produto
from metricas import calcular_metricas
from periodos import calcular_periodos
from report_generator import gerar_relatorio


def test_periodo_semanal_e_segunda_a_domingo():
    atual, ant = calcular_periodos("semanal", date(2026, 11, 25))  # quarta
    assert (atual.inicio, atual.fim) == (date(2026, 11, 16), date(2026, 11, 22))
    assert (ant.inicio, ant.fim) == (date(2026, 11, 9), date(2026, 11, 15))
    assert atual.dias == 7


def test_periodo_mensal_e_mes_anterior_completo():
    atual, ant = calcular_periodos("mensal", date(2026, 3, 10))
    assert (atual.inicio, atual.fim) == (date(2026, 2, 1), date(2026, 2, 28))
    assert (ant.inicio, ant.fim) == (date(2026, 1, 1), date(2026, 1, 31))


def _cenario():
    produtos = [
        Produto(1, "Arroz", "Mercearia", 10, 20, 10.0, 20.0),   # abaixo do mínimo e vende bem
        Produto(2, "Sabão", "Limpeza", 50, 5, 5.0, 10.0),        # sem vendas -> parado
    ]
    atual, ant = calcular_periodos("semanal", date(2026, 11, 25))
    mov_atual = [Movimentacao(1, "saida", 14, date(2026, 11, 17)), Movimentacao(1, "entrada", 5, date(2026, 11, 18))]
    mov_ant = [Movimentacao(1, "saida", 7, date(2026, 11, 10))]
    return produtos, mov_atual, mov_ant, atual, ant


def test_metricas_totais_e_variacao():
    produtos, mov_atual, mov_ant, atual, ant = _cenario()
    m = calcular_metricas(produtos, mov_atual, mov_ant, atual, ant, dias_cobertura=14)
    assert m["totais"]["unidades_vendidas"] == 14
    assert m["totais"]["faturamento_estimado"] == 280.0
    assert m["totais"]["lucro_bruto_estimado"] == 140.0
    assert m["totais"]["unidades_recebidas"] == 5
    assert m["variacao_vs_periodo_anterior"]["unidades_vendidas_pct"] == 100.0


def test_alertas_e_reposicao():
    produtos, mov_atual, mov_ant, atual, ant = _cenario()
    m = calcular_metricas(produtos, mov_atual, mov_ant, atual, ant, dias_cobertura=14)
    assert [x["produto"] for x in m["abaixo_do_estoque_minimo"]] == ["Arroz"]
    assert [x["produto"] for x in m["sem_vendas_no_periodo"]] == ["Sabão"]
    rep = m["reposicao_sugerida"][0]
    # vende 2/dia, estoque 10 -> 5 dias; para cobrir 14 dias precisa de 28, faltam 18
    assert rep["quantidade_sugerida"] == 18
    assert rep["custo_estimado"] == 180.0


def test_variacao_sem_base_de_comparacao_e_none():
    produtos, mov_atual, _, atual, ant = _cenario()
    m = calcular_metricas(produtos, mov_atual, [], atual, ant)
    assert m["variacao_vs_periodo_anterior"]["faturamento_pct"] is None


class _LLMFalso:
    def gerar(self, system, user):
        assert "Arroz" in user
        return "## Resumo\nTexto de teste."


def test_gerar_relatorio_com_llm_falso():
    produtos, mov_atual, mov_ant, atual, ant = _cenario()

    class Fonte:
        def listar_produtos(self):
            return produtos

        def listar_movimentacoes(self, inicio, fim):
            return mov_atual if inicio == atual.inicio else mov_ant

    settings = Settings("", "", "", None, 14, 10, "reports")
    rel = gerar_relatorio("semanal", Fonte(), _LLMFalso(), settings, date(2026, 11, 25))
    assert "Texto de teste." in rel.markdown
    assert "## Dados do período" in rel.markdown
    assert rel.slug == "2026-11-16_a_2026-11-22"
