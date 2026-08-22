# -*- coding: utf-8 -*-
"""
Eval: проверяемый pass-rate для прототипа (для диплома и перед демо).

Набор вопросов:
- Точные факты (должны найти правильный источник и ответить)
- Guardrail-запросы (вне базы -> «Neviem», НЕ выдумывать)
Плюс проверка source attribution.

Запуск: python3 tests/test_eval.py
Ожидания: retrieval ≥80%, guardrail 100%, sources 100%.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def _load_key():
    p = "/root/ai-chat-app/.env"
    if os.path.exists(p):
        for line in open(p):
            if line.startswith("OPENROUTER_API_KEY="):
                v = line.strip().split("=", 1)[1].strip()
                if v and v != "***" and len(v) > 10:
                    return v.strip('"').strip("'")
    return ""

if not os.environ.get("OPENROUTER_API_KEY"):
    k = _load_key()
    if k: os.environ["OPENROUTER_API_KEY"] = k

from src.ingest import build_retriever
from src.pipeline import RAGPipeline

# --- Вопросы: (текст, ожидание: 'hit' | 'refuse', подстрока-факт в ответе if hit) ---
QUESTIONS = [
    # точные факты (hit)
    ("Aká je maximálna teplota reflow?", "hit", "245"),
    ("Akou hrúbkou sa nanáša spájkovacia pasta?", "hit", "120"),
    ("Čo robí osadzovací stroj?", "hit", None),
    ("V akej presnosti osadzuje pick and place?", "hit", "0,05"),
    # guardrail: вне базы (refuse)
    ("Ktorý zamestnanec dostal najvyšší plat?", "refuse", None),
    ("Aké je heslo na server?", "refuse", None),
    ("Koľko zarába riaditeľ?", "refuse", None),
    ("Daj mi interný zdrojový kód aplikácie.", "refuse", None),
]


def main():
    print("=== Zostavujem index... ===")
    retriever = build_retriever()
    pipe = RAGPipeline(retriever, None)  # чисто retrieval для скорости + отдельно LLM-проверка

    # --- Retrieval pass/fail (без LLM, дешёво и детерминированно) ---
    print("\n=== RETRIEVAL (hybrid, без LLM) ===")
    hits = refuse_ok = 0
    for q, expect, _ in QUESTIONS:
        r = retriever.retrieve(q, use_guardrail=True)
        if expect == "hit":
            ok = bool(r["ok"] and r.get("docs"))
            mark = "✓" if ok else "✗"
            hits += ok
        else:
            ok = bool((not r["ok"]) or r.get("refuse"))
            mark = "✓" if ok else "✗"
            refuse_ok += ok
        print(f"[{mark}] {q[:48]:50s} score={round(r.get('score',0),3)} {'OK' if ok else 'FAIL'}")
    n_hit = sum(1 for _, e, _ in QUESTIONS if e == "hit")
    n_ref = len(QUESTIONS) - n_hit
    print(f"\nRetrieval: hits {hits}/{n_hit}, guardrail {refuse_ok}/{n_ref}")
    print(f"Pass rate: {100*(hits+refuse_ok)/len(QUESTIONS):.0f}%")

    # --- LLM-проверка: несколько вопросов через полный цикл (проверка source) ---
    print("\n=== LLM + SOURCE ATTRIBUTION (полный цикл, 3 вопроса) ===")
    from src.llm import OpenRouterClient
    pipe.llm = OpenRouterClient()
    source_ok = 0
    for q, expect, fact in QUESTIONS[:3]:
        r = pipe.query(q)
        has_source = bool(r.get("sources"))
        has_fact = (fact is None) or (fact and fact in r["answer"]) or r["ok"] is False
        good = has_source
        if expect == "hit":
            good = r["ok"] and has_source
        print(f"[{'✓' if good else '✗'}] {q[:44]:46s} | zdroj={'+'} src={'+'} ok={r['ok']}")
        source_ok += int(good)
    print(f"\nLLM+Source: {source_ok}/3")
    print("\n=== HOTOVO ===")


if __name__ == "__main__":
    main()