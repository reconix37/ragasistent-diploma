# -*- coding: utf-8 -*-
"""
LLM-клиент через OpenRouter (OpenAI-совместимый API).

Генерация ответа идёт через API (скорость + качество на демо),
а эмбеддинги и поиск — локально (приватность данных, «docs не покидают фирму»).
Ключ берётся из окружения OPENROUTER_API_KEY.
"""
from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

DEFAULT_MODEL = "openai/gpt-4o-mini"   # быстрый, дешёвый, хорош для демо


def _load_dotenv_key(path: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir, ".env")) -> str:
    """Достаёт OPENROUTER_API_KEY из .env в корне проекта (если есть)."""
    try:
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if line.startswith("OPENROUTER_API_KEY") and "=" in line:
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""

# fallback-цепочка: если основной молчит/падает, пробуем запасной
FALLBACK_MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-haiku",
    "meta-llama/llama-3.1-8b-instruct",
]

REFUSAL_REASONS = {
    "low_relevance": "Neviem, túto informáciu v poskytnutej dokumentácii nemám. V doteraz spracovaných dokumentoch sa takáto informácia nenachádza.",
    "no_index": "Databáza dokumentov ešte nie je vytvorená. Najprv nahrajte dokumenty.",
    "no_results": "Nenašiel som žiadne relevantné časti dokumentácie k tejto otázke.",
}


class OpenRouterClient:
    def __init__(self, model: str = DEFAULT_MODEL,
                 api_key: Optional[str] = None):
        key = api_key or os.environ.get("OPENROUTER_API_KEY") or _load_dotenv_key()
        if not key:
            raise ValueError(
                "Нет ключа OpenRouter. Задай OPENROUTER_API_KEY "
                "в окружении или в файле .env рядом с проектом "
                "(пример — файл .env.example)."
            )
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
        )
        self.model = model

    def generate(self, prompt: str, temperature: float = 0.2,
                 max_tokens: int = 300) -> str:
        """Один вызов LLM с ретраями по цепочке fallback."""
        models = [self.model, *FALLBACK_MODELS]
        last_err: Optional[str] = None
        for m in models:
            try:
                resp = self.client.chat.completions.create(
                    model=m,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Si AI asistent pre technickú dokumentáciu. "
                                "Odpovedaj vecne, podľa kontextu, s uvedením zdroja."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return (resp.choices[0].message.content or "").strip()
            except Exception as e:  # noqa: BLE001
                last_err = f"{type(e).__name__}: {e}"
                continue
        raise RuntimeError(f"LLM недоступен ({last_err})")

    def refusal_for(self, reason: str) -> str:
        return REFUSAL_REASONS.get(reason, REFUSAL_REASONS["no_results"])