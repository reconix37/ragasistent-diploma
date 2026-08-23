# -*- coding: utf-8 -*-
"""
Полный query-цикл RAG-ассистента (без UI) — единая точка входа,
которую тестирует eval и использует Streamlit-приложение.

query(q) -> {answer, ok, reason, sources, score, guardrail}
"""
from __future__ import annotations

import logging
from typing import Optional

from .guardrails import build_prompt, format_answer, is_empty_bad, is_refusal, loop_filter
from .llm import OpenRouterClient
from .retrieval import HybridRetriever

log = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self, retriever: HybridRetriever,
                 llm: Optional[OpenRouterClient] = None,
                 max_reruns: int = 2):
        self.retriever = retriever
        self.llm = llm            # может быть None -> тогда чисто retrieval-демо
        self.max_reruns = max_reruns

    def query(self, question: str, use_guardrail: bool = True) -> dict:
        # Шаг 1: retrieval (hybrid + rerank + guardrail-порог)
        r = self.retriever.retrieve(question, use_guardrail=use_guardrail)

        if not r["ok"]:
            # низкая релевантность / нет документации -> отказ (guardrail)
            return {
                "answer": (self.llm.refusal_for(r.get("reason", "no_results"))
                           if self.llm else _neviem_manual()),
                "ok": False,
                "reason": r.get("reason", "no_results"),
                "sources": [d.source for d in r.get("docs", [])],
                "score": r.get("score", 0.0),
                "guardrail": r.get("refuse", False) or r["reason"] == "low_relevance",
            }

        docs = r["docs"]
        # Шаг 2: нет LLM -> возвращаем найденные чанки (для eval retrieval без API)
        if not self.llm:
            return {
                "answer": f"[{len(docs)} relevantných častí]",
                "ok": True,
                "reason": "retrieval_only",
                "sources": [d.source for d in docs],
                "score": r["score"],
                "guardrail": False,
                "docs": docs,
            }

        # Шаг 3: генерация с loop-контролем качества
        prompt = build_prompt(question, docs)
        attempts: list = []
        answer = ""

        for _ in range(self.max_reruns):
            try:
                answer = self.llm.generate(prompt)
            except RuntimeError as e:
                log.warning("LLM call failed: %s", e)
                answer = ""
            attempts.append(answer)
            # loop_filter: N подряд некачественных -> отказ
            refused = loop_filter(attempts)
            if refused:
                return {
                    "answer": refused,
                    "ok": False,
                    "reason": "loop_refuse",
                    "sources": [d.source for d in docs],
                    "score": r["score"],
                    "guardrail": True,
                    "docs": docs,
                }
            if not is_empty_bad(answer):
                break

        # Шаг 4: пост-обработка + source attribution
        answer = format_answer(answer, docs)
        return {
            "answer": answer,
            "ok": True,
            "reason": "ok",
            "sources": [d.source for d in docs],
            "score": r["score"],
            "guardrail": False,
            "docs": docs,
        }

    def query_stream(self, question: str, use_guardrail: bool = True):
        """Стрим-версия query: выдаёт чанки ответа, затем словарь-метаданные.

        Используется в UI для живого рендера (st.write_stream). Собирает
        retrieval + guardrail так же, как query(), но LLM-часть — стримом.
        """
        r = self.retriever.retrieve(question, use_guardrail=use_guardrail)

        # guardrail-отказ
        if not r["ok"]:
            if self.llm:
                answer = self.llm.refusal_for(r.get("reason", "no_results"))
            else:
                answer = _neviem_manual()
            yield answer
            yield {
                "answer": answer,
                "ok": False,
                "reason": r.get("reason", "no_results"),
                "sources": [d.source for d in r.get("docs", [])],
                "score": r.get("score", 0.0),
                "guardrail": r.get("refuse", False) or r["reason"] == "low_relevance",
            }
            return

        docs = r["docs"]

        # нет LLM -> retrieval-only
        if not self.llm:
            answer = f"[{len(docs)} relevantných častí]"
            yield answer
            yield {
                "answer": answer,
                "ok": True,
                "reason": "retrieval_only",
                "sources": [d.source for d in docs],
                "score": r["score"],
                "guardrail": False,
                "docs": docs,
            }
            return

        # LLM-генерация стримом (без loop-контроля в стриме — ответ один,
        # форматирование источников в UI). Пост-обработка форматом — в конце.
        prompt = build_prompt(question, docs)
        raw = ""
        for chunk in self.llm.generate_stream(prompt):
            raw += chunk
            yield chunk

        answer = format_answer(raw, docs)
        # LLM могла сама отказаться («Neviem…») — тогда это тоже guardrail-отказ:
        # прячем источники и показываем оранжевую строку в UI.
        refused = is_refusal(answer)
        yield {
            "answer": answer,
            "ok": True,
            "reason": "refused" if refused else "ok",
            "sources": [] if refused else [d.source for d in docs],
            "score": r["score"],
            "guardrail": refused,
            "docs": docs,
        }


def _neviem_manual() -> str:
    return ("Neviem, túto informáciu v poskytnutej dokumentácii nemám. "
            "Uveďte prosím presnejšiu otázku alebo odkaz na komponent.")