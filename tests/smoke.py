# -*- coding: utf-8 -*-
"""Быстрый смоук-тест retrieval (без LLM): проверяем поиск + guardrail."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ingest import build_retriever

retriever = build_retriever()
print(f"\n=== Индекс: {len(retriever.docs)} чанков ===\n")

# Вопросы: 2 точных, 1 общий, 1 вне базы (guardrail)
questions = [
    ("Aká je maximálna teplota reflow? (точный)", "reflow"),
    ("Akou hrúbkou sa nanáša pasta? (точный)", "pasta"),
    ("Čo robí osadzovací stroj? (общий)", "osadzovací"),
    ("Ktorý zamestnanec dostal najvyšší plat? (вне базы → guardrail)", None),
]

for q, expect in questions:
    r = retriever.retrieve(q, use_guardrail=True)
    ok = r["ok"]
    srcs = [d.source for d in r.get("docs", [])]
    sc = round(r.get("score", 0), 3)
    mark = "✓" if (ok and expect) or (not ok and expect is None) else "?"
    print(f"[{mark}] {'ОТВЕЧАЕМ' if ok else 'REFUSE'} score={sc} | {q[:45]}")
    if srcs: print(f"      источники: {srcs}")
    if r.get("reason")=="low_relevance": print("      → guardrail «Neviem» сработал")

print("\nСмоук-тест завершён.")