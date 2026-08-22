# -*- coding: utf-8 -*-
"""
Streamlit UI для RAG-ассистента (демо для TESLA Stropkov).

Запуск:  streamlit run app.py
Чат: вопрос -> ответ + источник + метка guardrail.
Кнопка сброса и подсказки-примеры вопросов.
Секреты берутся из файла .env в корне проекта (если есть) — см. .env.example.
"""
from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.ingest import build_retriever
from src.llm import OpenRouterClient
from src.pipeline import RAGPipeline

# ---- мягкий подхват .env (если лежит рядом) -----------------------------
def _load_dotenv(path: str = os.path.join(os.path.dirname(__file__), ".env")):
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


_load_dotenv()

st.set_page_config(page_title="RAG Asistent — Technická dokumentácia",
                   page_icon="🔧", layout="centered")

# ---------- Шапка ----------
st.title("🔧 RAG Asistent")
st.caption("Asistent pre technickú dokumentáciu (dipolomová práca — RAG + guardrails + hybrid search)")


# ---------- Инициализация (кэш) ----------
@st.cache_resource(show_spinner=False)
def load_pipeline() -> RAGPipeline:
    """Грузит ретривер + LLM один раз (модель ~470 МБ и индексы в память)."""
    retriever = build_retriever()
    llm = None
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        try:
            llm = OpenRouterClient()
        except Exception:  # noqa: BLE001
            llm = None
    return RAGPipeline(retriever=retriever, llm=llm)


if "pipe" not in st.session_state:
    with st.spinner("Načítavam dokumentáciu a modely..."):
        st.session_state.pipe = load_pipeline()

pipe: RAGPipeline = st.session_state.pipe
llm_ok = pipe.llm is not None

# ---------- Инфо об индексе ----------
n_chunks = len(pipe.retriever.docs)
st.sidebar.markdown(f"**Index:** {n_chunks} častí z technickej dokumentácie")
st.sidebar.caption("Hybrid search (vector + BM25 + rerank) + guardrails")
if not llm_ok:
    st.sidebar.warning("⚠️ OPENROUTER_API_KEY не задан — режим поиска без LLM.")
st.sidebar.divider()

# ---------- Подсказки ----------
examples = [
    "Aká je maximálna teplota reflow?",
    "Akou hrúbkou sa nanáša spájkovacia pasta?",
    "Čo robí osadzovací stroj?",
    "Ktorý zamestnanec dostal najvyšší plat?",  # демо: должен ответить «Neviem»
]

# ---------- Чат ----------
if "messages" not in st.session_state:
    st.session_state.messages = []


def ask(question: str):
    """Прогон вопроса через пайплайн и запись в историю чата."""
    st.session_state.messages.append({"role": "user", "content": question})
    res = pipe.query(question)
    guardrail = bool(res.get("guardrail"))
    answer = res["answer"]
    sources = res.get("sources") or []
    if sources:
        answer += f"\n\n🔗 **Zdroj:** " + " | ".join(sources)
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "guardrail": guardrail,
        "sources": sources,
        "ok": res.get("ok"),
    })


# кнопка-пример в сайдбаре: ставит пример в чат и прогоняет
example_q = None
if st.sidebar.button("Vložiť príklad otázky"):
    example_q = examples[0]
if example_q:
    ask(example_q)

# рендер истории с метками guardrail
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant" and m.get("guardrail"):
            st.caption("🛡️ **Guardrail:** nízka relevancia — odpoveď odmietnutá.")
        elif m["role"] == "assistant" and not m.get("ok", True) and m.get("sources"):
            pass  # источник уже в тексте

# кнопка-промпт в чате
prompt = st.chat_input("Napíšte otázku k technickej dokumentácii...")
if prompt:
    ask(prompt)

# кнопка сброса чата
if st.session_state.messages:
    if st.sidebar.button("🗑️ Vymazať chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()