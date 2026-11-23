"""Configuração do módulo de relatórios com IA (lida de variáveis de ambiente / .env)."""
import os
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv é opcional
    pass


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    database_url: Optional[str]
    dias_cobertura: int
    max_itens: int
    output_dir: str


def get_settings() -> Settings:
    return Settings(
        api_key=os.getenv("GROQ_API_KEY", ""),
        base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        # O nome do modelo muda com o tempo: confira o atual no console da Groq.
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        database_url=os.getenv("DATABASE_URL") or None,
        dias_cobertura=int(os.getenv("DIAS_COBERTURA", "14")),
        max_itens=int(os.getenv("MAX_ITENS", "10")),
        output_dir=os.getenv("OUTPUT_DIR", "reports"),
    )
