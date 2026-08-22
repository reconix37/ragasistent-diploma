# -*- coding: utf-8 -*-
"""Полный цикл с LLM: retrieval -> генерация -> source attribution -> guardrail."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# подтянуть ключ из ai-chat-app (не хардкожу, не печатаю сам ключ)
def _load_key():
    # настоящий ключ в корневом .env (backend/.env содержит заглушку ***)
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
from src.llm import OpenRouterClient
from src.pipeline import RAGPipeline

print("=== Загрузка модели и индекса (может занять ~30 с) ===")
retriever = build_retriever()
llm = OpenRouterClient()          # бросит ошибку, если ключа нет
pipe = RAGPipeline(retriever, llm)
print(f"✓ Индекс: {len(retriever.docs)} чанков, LLM готов\n")

questions = [
    "Aká je maximálna teplota reflow pre SnAgCu pastu?",
    "Z ktorého dokumentu pochádza údaj o hrúbke pasty?",
    "Ktorý zamestnanec dostal najvyšší plat minulý mesiac?",  # guardrail
]

for q in questions:
    print("─"*60)
    print("OTÁZKA:", q)
    r = pipe.query(q)
    status = "✅ отвечаю" if r["ok"] else f"🛡️ отказ ({r['reason']})"
    print("  ", status, f"| score={round(r['score'],3)}")
    print("  ОТВЕТ:", r["answer"][:180])
    print("  ИСТОЧНИКИ:", r.get("sources"))
    print()
print("Полный цикл завершён.")