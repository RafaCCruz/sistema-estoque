# Relatórios com IA

Módulo que gera o **resumo semanal e mensal** do estoque em português, usando IA (Groq, plano gratuito).

## Como funciona
1. O código busca produtos e movimentações (banco ou dados de demonstração).
2. `metricas.py` calcula os números: vendas, faturamento e lucro estimados, mais vendidos, itens abaixo do mínimo, itens parados e reposição sugerida. **Sem IA, tudo determinístico.**
3. A IA recebe só esses números já agregados e escreve o texto do relatório. Ela não acessa o banco e não altera nada.
4. O relatório é salvo em Markdown (`reports/`) com o texto da IA **e** as tabelas de dados, para conferir os números.

Enviar só dados agregados (cerca de 2 mil tokens) mantém o uso dentro dos limites do plano gratuito e evita mandar dados de clientes para fora.

## Períodos
- **semanal**: última semana completa (segunda a domingo), comparada com a anterior.
- **mensal**: último mês completo, comparado com o anterior.

## Instalação
```bash
cd ai-reports
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # e preencha GROQ_API_KEY
```
Crie a chave gratuita em https://console.groq.com (não precisa de cartão).

## Uso
```bash
python main.py --tipo semanal --demo --dry-run   # mostra o prompt, sem chamar a IA
python main.py --tipo semanal --demo --sem-ia    # só as tabelas, sem IA
python main.py --tipo semanal --demo             # relatório com IA, dados fictícios
python main.py --tipo mensal                     # usa o banco (DATABASE_URL)
python main.py --tipo semanal --ate 2026-11-25   # define a data de referência
```

## Testes
```bash
pip install pytest && pytest
```

## Arquivos
| Arquivo | Função |
|---|---|
| `main.py` | linha de comando |
| `report_generator.py` | orquestra e salva o relatório |
| `metricas.py` | cálculo dos números |
| `periodos.py` | semana/mês e período anterior |
| `prompts.py` | instruções e prompt da IA (ajuste o tom aqui) |
| `llm_client.py` | cliente de IA (API estilo OpenAI) |
| `data_source.py` | fonte de dados: demo e SQL |
| `config.py` | variáveis de ambiente |

## Trocar de provedor de IA
O cliente usa a API compatível com OpenAI. Para trocar, mude apenas o `.env`:
- **OpenRouter**: `GROQ_BASE_URL=https://openrouter.ai/api/v1` + chave e modelo `...:free`
- **Ollama local**: `GROQ_BASE_URL=http://localhost:11434/v1`, `GROQ_API_KEY=ollama`, `GROQ_MODEL=qwen3:8b`

Os limites do plano gratuito e os nomes de modelos mudam com frequência: confira no console do provedor.

## Próximos passos
- Ajustar as consultas em `data_source.py` ao esquema final da pasta `database/`.
- Expor a geração como endpoint do backend e guardar os relatórios numa tabela (evita chamar a IA de novo).
- Agendar a execução (semanal às segundas, mensal no dia 1).
- Detecção de anomalias e previsão de demanda.

## Cuidados
- Nunca suba o arquivo `.env` (já está no `.gitignore`).
- Não envie nome, CPF ou contato de clientes para APIs externas (LGPD).
- Faturamento e lucro são **estimativas**: usam o preço de venda e de custo atuais do produto.
