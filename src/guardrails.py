# -*- coding: utf-8 -*-
"""
Guardrails: защита от галлюцинаций и контроль качества ответа.

Это то, что делает прототип НЕ «обычным чатом с PDF», а инженерной системой,
и является ядром дипломной работы (guardrails + loop engineering).

Уровни:
1. low_relevance  — порог релевантности (в retrieval.py).
2. refuse_phrase  — если ответ LLM не опирается на контекст (эвристика).
3. empty_bad      — пустой/неосмысленный ответ LLM -> безопасный дефолт.
4. source_attrib  — каждый ответ подписан источником (откуда взят факт).
5. loop           — «плохой ответ» -> повторный вызов или отказ (ограничено N).
"""
from __future__ import annotations

from typing import List, Optional

# Фразы-отказники, говорящие «я не знаю» (по-словацки — наш домен)
REFUSE_PHRASES = [
    "neviem",
    "nemám informácie",
    "nenájdené v dokumentácii",
    "nie je v dokumentácii",
    "nemám túto informáciu",
    "nemôžem odpovedať",
    "žiadne informácie",
]

# Если ответ слишком короткий / пустой -> считаем невалидным
EMPTY_THRESHOLD = 15   # символов

NEVIEM_ANSWER = (
    "Neviem, túto informáciu v poskytnutej dokumentácii nemám. "
    "Skúste preformulovať otázku alebo uviesť presnejší názov komponentu."
)


def is_refusal(text: str) -> bool:
    """Поймал ли LLM-ответ сигнал «не знаю» (как безопасный, так и честный)."""
    low = (text or "").lower()
    return any(p in low for p in REFUSE_PHRASES)


def is_empty_bad(text: str) -> bool:
    """Пустой/мусорный ответ."""
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    if len(cleaned) < EMPTY_THRESHOLD:
        return True
    # только символы-заглушки
    if cleaned.lower() in {"ok", "n/a", "-", "none", "nie"}:
        return True
    return False


def build_prompt(question: str, docs: List, lang: str = "sk") -> str:
    """Собирает промпт с контекстом только из релевантных чанков."""
    context = "\n\n".join(
        f"[Dokument: {d.source}] {d.text}" for d in docs
    )
    instr = (
        "Odpovedzaj LEN podľa uvedeného kontextu. "
        "Ak odpoveď nie je v kontexte, povedz: "
        '"Neviem, túto informáciu v dokumentácii nemám."'
    )
    return f"{instr}\n\nKontext:\n{context}\n\nOtázka: {question}\nOdpoveď:"


def format_answer(raw: str, docs: List) -> str:
    """
    Пост-обработка: чистит ответ, отсекает болтовню «вне контекста».
    Источники НЕ дописываются в текст — их рендерит UI отдельным блоком
    (аккордеон) из payload.sources.
    """
    text = (raw or "").strip()
    if is_empty_bad(text):
        return NEVIEM_ANSWER
    # отсекаем служебную строку "Zdroj: ...", которую LLM мог добавить сам
    # (в UI источники показываются аккуратно в аккордеоне, не в тексте)
    for marker in ("Zdroj:", "Zdroj :", "zdroj:"):
        idx = text.rfind(marker)
        if idx > 0:
            text = text[:idx].rstrip()
            break
    return text


def loop_filter(attempts: List[str], n_fail_before_refuse: int = 2) -> Optional[str]:
    """
    Loop engineering: после N некачественных ответов подряд -> отказ.
    (Ровно «LLM в цикле — как жечь токены», но с контролем state.)
    """
    bad = 0
    for a in attempts:
        if is_empty_bad(a) or is_refusal(a):
            bad += 1
        else:
            bad = 0
        if bad >= n_fail_before_refuse:
            return NEVIEM_ANSWER
    return None