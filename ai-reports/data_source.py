"""Fontes de dados do estoque.

FonteDemo  -> dados fictícios, para testar sem banco.
FonteSQL   -> lê do banco (PostgreSQL) via DATABASE_URL. Ajuste as consultas
              abaixo quando o esquema final da pasta /database estiver pronto.

Esquema esperado (nomes provisórios):
  produtos(id, nome, categoria, estoque_atual, estoque_minimo, preco_custo, preco_venda)
  movimentacoes(produto_id, tipo, quantidade, data)   -- tipo: 'entrada' | 'saida' | 'ajuste'
"""
import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List


@dataclass(frozen=True)
class Produto:
    id: int
    nome: str
    categoria: str
    estoque_atual: int
    estoque_minimo: int
    preco_custo: float
    preco_venda: float


@dataclass(frozen=True)
class Movimentacao:
    produto_id: int
    tipo: str  # 'entrada' | 'saida' | 'ajuste'
    quantidade: int
    data: date


class FonteDemo:
    """Dados fictícios e determinísticos de um pequeno comércio."""

    _CATALOGO = [
        ("Arroz 5kg", "Mercearia", 18.0, 26.9), ("Feijão 1kg", "Mercearia", 5.5, 8.9),
        ("Açúcar 1kg", "Mercearia", 3.2, 5.5), ("Óleo de soja 900ml", "Mercearia", 5.8, 8.5),
        ("Macarrão 500g", "Mercearia", 2.4, 4.5), ("Café 500g", "Mercearia", 12.0, 18.9),
        ("Leite integral 1L", "Laticínios", 3.6, 5.8), ("Queijo mussarela kg", "Laticínios", 29.0, 44.9),
        ("Iogurte 170g", "Laticínios", 1.8, 3.5), ("Manteiga 200g", "Laticínios", 8.0, 13.9),
        ("Refrigerante 2L", "Bebidas", 5.5, 9.5), ("Suco de caixa 1L", "Bebidas", 4.0, 7.2),
        ("Água mineral 1,5L", "Bebidas", 1.5, 3.0), ("Cerveja lata 350ml", "Bebidas", 2.9, 5.0),
        ("Sabão em pó 1kg", "Limpeza", 9.0, 15.9), ("Detergente 500ml", "Limpeza", 1.6, 3.2),
        ("Desinfetante 1L", "Limpeza", 4.0, 7.5), ("Papel higiênico 12un", "Limpeza", 14.0, 22.9),
        ("Pão de forma", "Padaria", 5.0, 8.9), ("Biscoito recheado", "Padaria", 2.0, 3.9),
        ("Shampoo 350ml", "Higiene", 8.0, 14.9), ("Sabonete 90g", "Higiene", 1.2, 2.5),
        ("Creme dental 90g", "Higiene", 3.0, 5.9), ("Desodorante aerosol", "Higiene", 7.5, 13.5),
    ]

    def __init__(self, referencia: date, semente: int = 42):
        rng = random.Random(semente)
        self._produtos: List[Produto] = []
        self._movs: List[Movimentacao] = []
        for i, (nome, cat, custo, venda) in enumerate(self._CATALOGO, start=1):
            demanda = rng.choice([0, 1, 2, 4, 6, 10])  # média diária de saída
            minimo = max(5, demanda * 5)
            estoque = rng.randint(0, minimo * 3)
            self._produtos.append(Produto(i, nome, cat, estoque, minimo, custo, venda))
            for d in range(1, 75):
                dia = referencia - timedelta(days=d)
                if demanda and rng.random() < 0.85:
                    self._movs.append(Movimentacao(i, "saida", max(1, int(rng.gauss(demanda, 1.5))), dia))
                if rng.random() < 0.05:
                    self._movs.append(Movimentacao(i, "entrada", rng.randint(20, 60), dia))

    def listar_produtos(self) -> List[Produto]:
        return list(self._produtos)

    def listar_movimentacoes(self, inicio: date, fim: date) -> List[Movimentacao]:
        return [m for m in self._movs if inicio <= m.data <= fim]


class FonteSQL:
    def __init__(self, database_url: str):
        from sqlalchemy import create_engine

        self._engine = create_engine(database_url)

    def listar_produtos(self) -> List[Produto]:
        from sqlalchemy import text

        sql = text(
            "SELECT id, nome, categoria, estoque_atual, estoque_minimo, preco_custo, preco_venda "
            "FROM produtos"
        )
        with self._engine.connect() as conn:
            return [
                Produto(r.id, r.nome, r.categoria or "Sem categoria", int(r.estoque_atual),
                        int(r.estoque_minimo), float(r.preco_custo), float(r.preco_venda))
                for r in conn.execute(sql)
            ]

    def listar_movimentacoes(self, inicio: date, fim: date) -> List[Movimentacao]:
        from sqlalchemy import text

        sql = text(
            "SELECT produto_id, tipo, quantidade, data FROM movimentacoes "
            "WHERE data >= :inicio AND data <= :fim"
        )
        with self._engine.connect() as conn:
            return [
                Movimentacao(r.produto_id, r.tipo, int(r.quantidade), r.data)
                for r in conn.execute(sql, {"inicio": inicio, "fim": fim})
            ]
