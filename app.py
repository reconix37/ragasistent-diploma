# -*- coding: utf-8 -*-
"""
Streamlit UI для RAG-ассистента (демо для TESLA Stropkov).

Запуск:  streamlit run app.py
Чат: вопрос -> ответ + источник + метка guardrail.
Секреты берутся из файла .env в корне проекта (если есть) — см. .env.example.

Оформление: Rosé Pine Dawn (base #faf4ed, surface #fffaf3), Space Grotesk + JetBrains Mono.
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

# ---------- ДИЗАЙН-СИСТЕМА (Rosé Pine Dawn) -------------------------------
CSS = """
<style>
/* ===== fonts ===== */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --rp-base:  #faf4ed;
  --rp-surface:#fffaf3;
  --rp-overlay:#f2e9de;
  --rp-muted: #9893a5;
  --rp-subtle:#797593;
  --rp-text: #575279;
  --rp-love: #b4637a;
  --rp-gold: #ea9d34;
  --rp-rose: #d7827e;
  --rp-pine: #286983;
  --rp-foam: #56949f;
  --rp-iris: #907aa9;
  --rp-hl-low: #f4ede8;
  --rp-hl-med:#dfdad9;
  --rp-hl-high:#cecacd;
}

/* ===== base ===== */
html, body, [data-testid="stAppViewContainer"] {
  background: var(--rp-base);
  color: var(--rp-text);
  font-family: 'Space Grotesk', system-ui, sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 780px; }

/* ===== typography ===== */
h1, h2, h3 { color: var(--rp-text); font-weight: 600; letter-spacing: -0.01em; }

/* ===== header ===== */
.header-mark { font-size: 1.75rem; font-weight: 700; color: var(--rp-text);
  letter-spacing: -0.02em; margin: 0; }
.header-sub { color: var(--rp-muted); font-size: 0.95rem; margin-top: -0.2rem; }
.header-divider { height: 3px; width: 56px; border-radius: 2px;
  background: linear-gradient(90deg, var(--rp-foam), var(--rp-iris));
  margin: 0.45rem 0 1.15rem 0; }

/* ===== status chip ===== */
.chip { display: inline-flex; align-items: center; gap: 0.45rem;
  font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
  padding: 0.32rem 0.75rem; border-radius: 999px;
  border: 1px solid var(--rp-hl-high); background: var(--rp-surface); color: var(--rp-text); }
.chip-dot { width: 8px; height: 8px; border-radius: 50%; }
.chip-on .chip-dot { background: var(--rp-pine); box-shadow: 0 0 0 3px rgba(40,105,131,.15); }
.chip-off .chip-dot { background: var(--rp-gold); box-shadow: 0 0 0 3px rgba(234,157,52,.18); }

/* ===== sidebar ===== */
[data-testid="stSidebar"] { background: var(--rp-surface);
  border-right: 1px solid var(--rp-hl-med); }
[data-testid="stSidebar"] * { color: var(--rp-text); }
.sb-title { font-weight: 700; font-size: 1.02rem; color: var(--rp-text);
  letter-spacing: -0.01em; margin-bottom: 0.1rem; }
.sb-meta { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
  color: var(--rp-muted); line-height: 1.55; }
.sb-sep { border-top: 1px solid var(--rp-hl-med); margin: 0.9rem 0; }
.sb-label { font-size: 0.72rem; font-weight: 600; color: var(--rp-subtle);
  text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.5rem; }

/* buttons */
[data-testid="stSidebar"] .stButton > button, .stButton > button {
  background: var(--rp-surface); border: 1px solid var(--rp-hl-high);
  color: var(--rp-text); border-radius: 10px;
  font-family: 'Space Grotesk', sans-serif; font-weight: 500;
  padding: 0.45rem 1rem; transition: all .15s ease; }
[data-testid="stSidebar"] .stButton > button:hover, .stButton > button:hover {
  border-color: var(--rp-foam); background: var(--rp-hl-low); color: var(--rp-pine); }
[data-testid="stSidebar"] .stButton > button:active, .stButton > button:active { transform: translateY(1px); }

/* ===== chat bubbles ===== */
[data-testid="stChatMessage"] { background: var(--rp-surface);
  border: 1px solid var(--rp-hl-med); border-radius: 14px;
  padding: 0.55rem 0.9rem; box-shadow: 0 1px 2px rgba(87,82,121,.05); }
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p { margin: 0.15rem 0; line-height: 1.6; }

/* source line */
.src-line { margin-top: 0.6rem; padding-top: 0.5rem;
  border-top: 1px dashed var(--rp-hl-med); }
.src-tag { display: inline-block; font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem; color: var(--rp-pine); background: rgba(40,105,131,.09);
  border: 1px solid rgba(40,105,131,.22); padding: 0.12rem 0.5rem;
  border-radius: 999px; margin: 0.15rem 0.2rem 0 0; }

/* guardrail note */
.gr-line { margin-top: 0.5rem; font-size: 0.85rem; color: var(--rp-gold); font-weight: 500; }

/* ===== chat input ===== */
[data-testid="stChatInput"] { border: 1px solid var(--rp-hl-high); border-radius: 12px;
  background: var(--rp-surface); }
[data-testid="stChatInput"]:focus-within { border-color: var(--rp-foam);
  box-shadow: 0 0 0 3px rgba(86,148,159,.15); }
[data-testid="stChatInput"] input { color: var(--rp-text); }
[data-testid="stChatInput"] input::placeholder { color: var(--rp-muted); }

/* misc */
a { color: var(--rp-foam); }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--rp-muted); }
</style>
"""

st.set_page_config(page_title="RAG Asistent — Technická dokumentácia",
                   page_icon="🔧", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

# ---------- Шапка ----------
st.markdown('<p class="header-mark">🔧 RAG Asistent</p>', unsafe_allow_html=True)
st.markdown('<p class="header-sub">Asistent pre technickú dokumentáciu — RAG + guardrails + hybrid search</p>',
            unsafe_allow_html=True)
st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)

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

# ---------- Логика чата ----------
if "messages" not in st.session_state:
    st.session_state.messages = []


def ask(question: str):
    """Прогон вопроса через пайплайн и запись в историю чата."""
    st.session_state.messages.append({"role": "user", "content": question})
    res = pipe.query(question)
    guardrail = bool(res.get("guardrail"))
    answer = res["answer"]
    sources = res.get("sources") or []
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "guardrail": guardrail,
        "sources": sources,
        "ok": res.get("ok"),
    })


# ---------- Сайдбар ----------
n_chunks = len(pipe.retriever.docs)
st.sidebar.markdown('<div class="sb-sep"></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sb-title">Index</div>', unsafe_allow_html=True)
st.sidebar.markdown(
    f'<div class="sb-meta">{n_chunks} častí<br>Hybrid search + BM25 + rerank<br>Guardrails: relevance threshold</div>',
    unsafe_allow_html=True)

if llm_ok:
    st.sidebar.markdown(
        '<span class="chip chip-on"><span class="chip-dot"></span>AI odpovede: ON</span>',
        unsafe_allow_html=True)
else:
    st.sidebar.markdown(
        '<span class="chip chip-off"><span class="chip-dot"></span>AI odpovede: OFF (search only)</span>',
        unsafe_allow_html=True)

st.sidebar.markdown('<div class="sb-sep"></div>', unsafe_allow_html=True)

# ---------- Подсказки ----------
examples = [
    "Aká je maximálna teplota reflow?",
    "Akou hrúbkou sa nanáša spájkovacia pasta?",
    "Čo robí osadzovací stroj?",
    "Ktorý zamestnanec dostal najvyšší plat?",  # демо: должен ответить «Neviem»
]

st.sidebar.markdown('<div class="sb-label">Skúste sa opýtať</div>', unsafe_allow_html=True)
for ex in examples:
    if st.sidebar.button(ex, use_container_width=True):
        ask(ex)

# ---------- Чат: рендер истории ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            if m.get("guardrail"):
                st.markdown('<div class="gr-line">🛡️ Guardrail: nízka relevancia — odpoveď odmietnutá.</div>',
                            unsafe_allow_html=True)
            elif m.get("sources"):
                tags = "".join(f'<span class="src-tag">📄 {s}</span>' for s in m["sources"])
                st.markdown(f'<div class="src-line">Zdroj: {tags}</div>', unsafe_allow_html=True)

# ---------- Чат: ввод ----------
prompt = st.chat_input("Napíšte otázku k technickej dokumentácii...")
if prompt:
    ask(prompt)

# ---------- Чат: сброс ----------
if st.session_state.messages:
    if st.sidebar.button("🗑️ Vymazať chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()