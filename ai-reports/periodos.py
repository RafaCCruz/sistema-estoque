"""Cálculo dos períodos do relatório (e do período anterior, para comparação)."""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Tuple


@dataclass(frozen=True)
class Periodo:
    inicio: date
    fim: date  # inclusive

    @property
    def dias(self) -> int:
        return (self.fim - self.inicio).days + 1

    def rotulo(self) -> str:
        return f"{self.inicio.strftime('%d/%m/%Y')} a {self.fim.strftime('%d/%m/%Y')}"


def calcular_periodos(tipo: str, referencia: date) -> Tuple[Periodo, Periodo]:
    """semanal: última semana completa (segunda a domingo) antes da data de referência.
    mensal: último mês completo antes da data de referência.
    Retorna (periodo_atual, periodo_anterior)."""
    if tipo == "semanal":
        segunda_atual = referencia - timedelta(days=referencia.weekday())
        fim = segunda_atual - timedelta(days=1)
        inicio = fim - timedelta(days=6)
        ant_fim = inicio - timedelta(days=1)
        ant_inicio = ant_fim - timedelta(days=6)
    elif tipo == "mensal":
        fim = referencia.replace(day=1) - timedelta(days=1)
        inicio = fim.replace(day=1)
        ant_fim = inicio - timedelta(days=1)
        ant_inicio = ant_fim.replace(day=1)
    else:
        raise ValueError("tipo deve ser 'semanal' ou 'mensal'")
    return Periodo(inicio, fim), Periodo(ant_inicio, ant_fim)
