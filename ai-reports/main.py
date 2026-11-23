"""Linha de comando do módulo de relatórios com IA.

Exemplos:
  python main.py --tipo semanal --demo --dry-run     # vê o prompt sem chamar a IA
  python main.py --tipo semanal --demo               # gera com a IA usando dados fictícios
  python main.py --tipo mensal                       # usa o banco (DATABASE_URL)
  python main.py --tipo semanal --sem-ia             # só as tabelas, sem IA
"""
import argparse
import sys
from datetime import date

from config import get_settings
from data_source import FonteDemo, FonteSQL
from llm_client import LLMClient, LLMError
from prompts import SYSTEM, montar_prompt_usuario
from report_generator import gerar_relatorio, salvar


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Gera o relatório semanal ou mensal de estoque com IA.")
    ap.add_argument("--tipo", choices=["semanal", "mensal"], required=True)
    ap.add_argument("--ate", help="data de referência AAAA-MM-DD (padrão: hoje)")
    ap.add_argument("--demo", action="store_true", help="usa dados fictícios em vez do banco")
    ap.add_argument("--dry-run", action="store_true", help="mostra o prompt e não chama a IA")
    ap.add_argument("--sem-ia", action="store_true", help="gera só as tabelas de dados")
    args = ap.parse_args(argv)

    settings = get_settings()
    referencia = date.fromisoformat(args.ate) if args.ate else date.today()

    if args.demo:
        fonte = FonteDemo(referencia)
    elif settings.database_url:
        fonte = FonteSQL(settings.database_url)
    else:
        print("Defina DATABASE_URL no .env ou use --demo.", file=sys.stderr)
        return 2

    try:
        if args.dry_run:
            rel = gerar_relatorio(args.tipo, fonte, None, settings, referencia)
            print(SYSTEM)
            print(montar_prompt_usuario(args.tipo, rel.metricas))
            return 0
        llm = None if args.sem_ia else LLMClient(settings)
        rel = gerar_relatorio(args.tipo, fonte, llm, settings, referencia)
    except LLMError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1

    caminho = salvar(rel, settings.output_dir)
    print(rel.markdown)
    print(f"\nRelatório salvo em {caminho}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
