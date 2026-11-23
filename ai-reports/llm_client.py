"""Cliente de IA. Usa a API compatível com OpenAI, então trocar de provedor
(Groq, OpenRouter, Ollama local...) é só mudar GROQ_BASE_URL, GROQ_API_KEY e GROQ_MODEL."""
from config import Settings


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, settings: Settings):
        if not settings.api_key:
            raise LLMError("GROQ_API_KEY não definida. Copie .env.example para .env e preencha.")
        from openai import OpenAI

        self._model = settings.model
        self._client = OpenAI(api_key=settings.api_key, base_url=settings.base_url, max_retries=3)

    def gerar(self, system: str, user: str) -> str:
        from openai import APIError, RateLimitError

        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                max_completion_tokens=1500,
            )
        except RateLimitError as e:
            raise LLMError("Limite do plano gratuito atingido (erro 429). Tente de novo mais tarde.") from e
        except APIError as e:
            raise LLMError(f"Falha ao chamar a IA: {e}") from e
        texto = (resp.choices[0].message.content or "").strip()
        if not texto:
            raise LLMError("A IA retornou uma resposta vazia.")
        return texto
