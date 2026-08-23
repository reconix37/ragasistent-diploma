# -*- coding: utf-8 -*-
"""
Streamlit UI для RAG-ассистента (демо для TESLA Stropkov).

Запуск:  streamlit run app.py
Чат: вопрос -> стрим-ответ -> источник (аккордеон с цитатой) + метка guardrail.
Секреты берутся из файла .env в корне проекта (если есть) — см. .env.example.

Оформление: Rosé Pine (Dawn — светлая / Moon — тёмная), переключатель темы в сайдбаре.
Шрифты: Space Grotesk (текст) + JetBrains Mono (метаданные).
"""
from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.ingest import DEFAULT_DOC_DIR, build_retriever
DOC_DIR = DEFAULT_DOC_DIR
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

# ---------- Аватары (SVG-круги с буквой, без эмодзи-слопа) ----------
def _svg_avatar(letter: str, bg: str, fg: str, size: int = 200) -> str:
    """Буква в цветном круге -> data-URI для st.chat_message(avatar=...)."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
           f'viewBox="0 0 {size} {size}"><circle cx="{size/2}" cy="{size/2}" '
           f'r="{size/2}" fill="{bg}"/><text x="{size/2}" y="{size/2}" '
           f'font-family="Space Grotesk, sans-serif" font-size="{size*0.55}" '
           f'font-weight="600" fill="{fg}" text-anchor="middle" '
           f'dominant-baseline="central">{letter}</text></svg>')
    from urllib.parse import quote
    return "data:image/svg+xml," + quote(svg)


def avatar_for(role: str) -> str:
    """Аватар зависит от темы (контрастная буква на акцентном фоне)."""
    if role == "assistant":
        return _svg_avatar("A", "#2f6f7d", "#ffffff")
    return _svg_avatar("R", "#6a4f8a", "#ffffff")


def _read_doc_text(source: str) -> str:
    """Читает исходный .md/.txt документ из docs/ по имени файла."""
    for ext in (".md", ".txt"):
        p = os.path.join(DOC_DIR, source)
        if os.path.exists(p):
            try:
                return open(p, encoding="utf-8").read().strip()
            except Exception:  # noqa: BLE001
                return ""
    # возможен путь с пробелами/без расширения в имени
    try:
        return open(os.path.join(DOC_DIR, source), encoding="utf-8").read().strip()
    except Exception:  # noqa: BLE001
        return ""


def _render_sources(sources: list, docs: list | None, uid: str):
    """Аккордеон с кликабельными источниками: клик по доку → открыть превью
    прямо на странице (session_state.open_doc).  uid — уникальный префикс ключа
    (индекс сообщения), чтобы одинаковые доки в разных ответах не давали
    дубли ключей Streamlit."""
    if "open_doc" not in st.session_state:
        st.session_state.open_doc = None
    for src in sources:
        key = f"src_{uid}_{src}"
        if st.button(f"📄 {src}", key=key, use_container_width=True,
                     type="secondary"):
            if st.session_state.open_doc == src:
                st.session_state.open_doc = None
            else:
                st.session_state.open_doc = src
            st.rerun()
    if docs:
        doc0 = docs[0]
        quote = (doc0.text or "")[:220]
        st.markdown(f'<div class="src-quote">"{quote}…"</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="src-meta">{doc0.source} · fragment</div>',
                    unsafe_allow_html=True)

# ---------- ДИЗАЙН-СИСТЕМА (Rosé Pine) -----------------------------------
CSS_LIGHT = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg:        #f2ece4;
  --surface:   #fffaf3;
  --surface-2: #f6f0e8;
  --border:    #d9d2c7;
  --border-2:  #c9c1b5;
  --text:      #44415a;
  --text-soft: #575279;
  --muted:     #7b7690;
  --faint:     #a29bb3;
  --accent:    #2f6f7d;
  --accent-2:  #56949f;
  --accent-3:  #6a4f8a;
  --good:      #286983;
  --warn:      #b26a3d;
  --bad:       #8a3f4f;
  --code-bg:   #f6f0e8;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg); color: var(--text);
  font-family: 'Space Grotesk', system-ui, sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.1rem; padding-bottom: 3rem; max-width: 760px; }

h1,h2,h3,h4 { color: var(--text-soft); letter-spacing: -0.01em; }
a { color: var(--accent); }

/* ---- header ---- */
.hd-mark { font-size: 1.6rem; font-weight: 700; color: var(--text);
  letter-spacing: -0.02em; margin: 0; }
.hd-sub { color: var(--muted); font-size: 0.92rem; margin-top: -0.15rem; }
.hd-div { height: 3px; width: 52px; border-radius: 3px; margin: 0.5rem 0 1.1rem 0;
  background: linear-gradient(90deg, var(--accent-2), var(--accent-3)); }

/* ---- chip (status) ---- */
.chip { display:inline-flex; align-items:center; gap:.45rem;
  font-family:'JetBrains Mono',monospace; font-size:.76rem;
  padding:.3rem .7rem; border-radius:8px; border:1px solid var(--border);
  background:var(--surface); color:var(--text-soft); }
.chip-dot { width:7px;height:7px;border-radius:50%; }
.chip-on .chip-dot { background:var(--good); }
.chip-off .chip-dot { background:var(--warn); }
.chip-no { background:var(--surface-2); color:var(--muted); }

/* ---- sidebar ---- */
[data-testid="stSidebar"] { background:var(--surface); border-right:1px solid var(--border); }
[data-testid="stSidebar"] * { color:var(--text-soft); }
.sb-title { font-weight:700; font-size:.98rem; color:var(--text); letter-spacing:-.01em; }
.sb-meta { font-family:'JetBrains Mono',monospace; font-size:.7rem; color:var(--muted); line-height:1.6; }
.sb-sep { border-top:1px solid var(--border); margin:.85rem 0; }
.sb-label { font-size:.7rem; font-weight:600; color:var(--faint);
  text-transform:uppercase; letter-spacing:.07em; margin-bottom:.45rem; }

/* buttons */
[data-testid="stSidebar"] .stButton>button, .stButton>button {
  background:var(--surface); border:1px solid var(--border); color:var(--text-soft);
  border-radius:8px; font-family:'Space Grotesk',sans-serif; font-weight:500;
  padding:.42rem .9rem; transition:all .14s ease; }
[data-testid="stSidebar"] .stButton>button:hover, .stButton>button:hover {
  border-color:var(--accent); background:var(--surface-2); color:var(--accent); }
[data-testid="stSidebar"] .stButton>button:active, .stButton>button:active { transform:translateY(1px); }

/* ---- chat bubbles (less round, stricter) ---- */
[data-testid="stChatMessage"] {
  background:var(--surface); border:1px solid var(--border);
  border-radius:10px; padding:.5rem .85rem;
  box-shadow:0 1px 2px rgba(0,0,0,.03);
  height:auto !important; min-height:0; overflow:visible; }
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p { margin:.15rem 0; line-height:1.6; color:var(--text); }
[data-testid="stChatMessageContent"] { overflow-wrap:break-word; overflow:visible; }
/* user bubble — subtle accent border */
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background:var(--surface-2); border-color:var(--border-2); }

/* avatar circles (letter only, no emoji) */
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
  border-radius:50% !important; background:var(--accent) !important;
  color:#fff !important; font-weight:600 !important;
  font-family:'Space Grotesk',sans-serif; }

/* ---- source accordion ---- */
[data-testid="stExpander"] { border:1px solid var(--border); border-radius:10px;
  background:var(--surface-2); }
[data-testid="stExpander"] details { background:transparent; }
[data-testid="stExpander"] summary { background:var(--surface-2); border-radius:10px; color:var(--text-soft); }
.src-meta { font-family:'JetBrains Mono',monospace; font-size:.72rem; color:var(--muted); margin-top:.1rem; }
.doc-title { font-weight:700; font-size:.98rem; color:var(--text); letter-spacing:-.01em; margin-bottom:.4rem; }
.doc-preview { font-size:.9rem; color:var(--text-soft); line-height:1.6;
  background:var(--surface-2); border:1px solid var(--border); border-radius:10px;
  padding:.9rem 1rem; max-height:320px; overflow-y:auto; white-space:pre-wrap; }
.src-quote { font-size:.85rem; color:var(--text-soft); border-left:2px solid var(--accent-2);
  padding-left:.6rem; margin:.3rem 0 0 0; line-height:1.55; }
.src-src { font-family:'JetBrains Mono',monospace; font-size:.74rem; color:var(--accent); margin-top:.35rem; }

/* ---- guardrail / neviem ---- */
.gr-line { margin:.6rem 0 .45rem 0; font-size:.84rem; color:var(--warn);
  font-weight:500; line-height:1.45; overflow-wrap:break-word; }

/* ---- chat input ---- */
[data-testid="stChatInput"] { border:1px solid var(--border-2); border-radius:10px; background:var(--surface); }
[data-testid="stChatInput"]:focus-within { border-color:var(--accent); box-shadow:0 0 0 3px rgba(47,111,125,.13); }
[data-testid="stChatInput"] input { color:var(--text); }
[data-testid="stChatInput"] input::placeholder { color:var(--faint); }

.stCaption, [data-testid="stCaptionContainer"] { color:var(--muted); }

/* thinking indicator (animated dots) */
.thinking { font-size:1.4rem; letter-spacing:.15em; color:var(--muted); animation: thinkpulse 1s steps(4) infinite; }
@keyframes thinkpulse { 0%{opacity:.3} 50%{opacity:1} 100%{opacity:.3} }

/* hide Community Cloud toolbar (Stop/Deploy/...) */
[data-testid="stToolbar"], [data-testid="stStatusWidget"],
div:has(> [data-testid="stToolbar"]) { display:none !important; }

/* toggle visibility on light theme */
[data-testid="stToggle"], [data-testid="stToggleSwitchContainer"] { opacity:1; }
section[data-testid="stSidebar"] [data-testid="stToggleSwitchContainer"] [data-baseweb="checkbox"] {
  background:var(--surface-2) !important; border:1px solid var(--border-2) !important; }
</style>
"""

CSS_DARK = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg:        #15171a;
  --surface:   #1c1f24;
  --surface-2: #23272d;
  --border:    #2d323a;
  --border-2:  #3a4049;
  --text:      #e6e1f0;
  --text-soft: #c9c2da;
  --muted:     #8f8aa0;
  --faint:     #6a6578;
  --accent:    #8db7c4;
  --accent-2:  #76aab8;
  --accent-3:  #ab9ac9;
  --good:      #7bb7c9;
  --warn:      #e0a46a;
  --bad:       #e39baa;
  --code-bg:   #23272d;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important; color: var(--text) !important;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.1rem; padding-bottom: 3rem; max-width: 760px; }
h1,h2,h3,h4 { color: var(--text-soft); letter-spacing:-0.01em; }
a { color: var(--accent); }
.hd-mark { font-size:1.6rem; font-weight:700; color:var(--text); letter-spacing:-0.02em; margin:0; }
.hd-sub { color:var(--muted); font-size:.92rem; margin-top:-.15rem; }
.hd-div { height:3px; width:52px; border-radius:3px; margin:.5rem 0 1.1rem 0;
  background:linear-gradient(90deg, var(--accent-2), var(--accent-3)); }
.chip { display:inline-flex; align-items:center; gap:.45rem; font-family:'JetBrains Mono',monospace;
  font-size:.76rem; padding:.3rem .7rem; border-radius:8px; border:1px solid var(--border);
  background:var(--surface); color:var(--text-soft); }
.chip-dot { width:7px;height:7px;border-radius:50%; }
.chip-on .chip-dot { background:var(--good); }
.chip-off .chip-dot { background:var(--warn); }
[data-testid="stSidebar"] { background:var(--surface) !important; border-right:1px solid var(--border); }
[data-testid="stSidebar"] * { color:var(--text-soft); }
.sb-title { font-weight:700; font-size:.98rem; color:var(--text); letter-spacing:-.01em; }
.sb-meta { font-family:'JetBrains Mono',monospace; font-size:.7rem; color:var(--muted); line-height:1.6; }
.sb-sep { border-top:1px solid var(--border); margin:.85rem 0; }
.sb-label { font-size:.7rem; font-weight:600; color:var(--faint); text-transform:uppercase; letter-spacing:.07em; margin-bottom:.45rem; }

[data-testid="stSidebar"] .stButton>button, .stButton>button {
  background:var(--surface); border:1px solid var(--border); color:var(--text-soft);
  border-radius:8px; font-family:'Space Grotesk',sans-serif; font-weight:500;
  padding:.42rem .9rem; transition:all .14s ease; }
[data-testid="stSidebar"] .stButton>button:hover, .stButton>button:hover {
  border-color:var(--accent); background:var(--surface-2); color:var(--accent); }
[data-testid="stSidebar"] .stButton>button:active, .stButton>button:active { transform:translateY(1px); }

[data-testid="stChatMessage"] {
  background:var(--surface); border:1px solid var(--border);
  border-radius:10px; padding:.5rem .85rem; box-shadow:0 1px 2px rgba(0,0,0,.2); }
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p { margin:.15rem 0; line-height:1.6; color:var(--text); }
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background:var(--surface-2); border-color:var(--border-2); }

[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
  border-radius:50% !important; background:var(--accent) !important;
  color:var(--bg) !important; font-weight:600 !important; font-family:'Space Grotesk',sans-serif; }

[data-testid="stExpander"] { border:1px solid var(--border); border-radius:10px; background:var(--surface-2); }
[data-testid="stExpander"] summary { background:var(--surface-2); border-radius:10px; color:var(--text-soft); }
.src-meta { font-family:'JetBrains Mono',monospace; font-size:.72rem; color:var(--muted); margin-top:.1rem; }
.doc-title { font-weight:700; font-size:.98rem; color:var(--text); letter-spacing:-.01em; margin-bottom:.4rem; }
.doc-preview { font-size:.9rem; color:var(--text-soft); line-height:1.6;
  background:var(--surface-2); border:1px solid var(--border); border-radius:10px;
  padding:.9rem 1rem; max-height:320px; overflow-y:auto; white-space:pre-wrap; }
.src-quote { font-size:.85rem; color:var(--text-soft); border-left:2px solid var(--accent-2); padding-left:.6rem; margin:.3rem 0 0 0; line-height:1.55; }
.src-src { font-family:'JetBrains Mono',monospace; font-size:.74rem; color:var(--accent); margin-top:.35rem; }

.gr-line { margin-top:.5rem; font-size:.84rem; color:var(--warn); font-weight:500; }

[data-testid="stChatInput"] { border:1px solid var(--border-2); border-radius:10px; background:var(--surface) !important; }
[data-testid="stChatInput"]:focus-within { border-color:var(--accent); box-shadow:0 0 0 3px rgba(141,183,196,.15); }
[data-testid="stChatInput"] input { color:var(--text); }
[data-testid="stChatInput"] input::placeholder { color:var(--faint); }

.stCaption, [data-testid="stCaptionContainer"] { color:var(--muted); }

/* thinking indicator (animated dots) */
.thinking { font-size:1.4rem; letter-spacing:.15em; color:var(--muted); animation: thinkpulse 1s steps(4) infinite; }
@keyframes thinkpulse { 0%{opacity:.3} 50%{opacity:1} 100%{opacity:.3} }

/* hide Community Cloud toolbar (Stop/Deploy/...) */
[data-testid="stToolbar"], [data-testid="stStatusWidget"],
div:has(> [data-testid="stToolbar"]) { display:none !important; }

/* toggle visibility on dark theme */
[data-testid="stToggle"], [data-testid="stToggleSwitchContainer"] { opacity:1; }
section[data-testid="stSidebar"] [data-testid="stToggleSwitchContainer"] [data-baseweb="checkbox"] {
  background:var(--surface-2) !important; border:1px solid var(--border-2) !important; }
</style>
"""

# ---------- Конфиг ----------
st.set_page_config(page_title="RAG Asistent — Technická dokumentácia",
                   page_icon="⚙︎", layout="centered")

# тема читается ДО инжекта CSS — нужный блок всегда идёт последним
if "theme" not in st.session_state:
    st.session_state.theme = "light"
_dark_request = st.sidebar.toggle("Tmavá téma",
                                  value=(st.session_state.theme == "dark"))
st.session_state.theme = "dark" if _dark_request else "light"

CSS = CSS_DARK if st.session_state.theme == "dark" else CSS_LIGHT
st.markdown(CSS, unsafe_allow_html=True)

# ---------- Шапка ----------
st.markdown('<p class="hd-mark">RAG Asistent</p>', unsafe_allow_html=True)
st.markdown('<p class="hd-sub">Asistent pre technickú dokumentáciu — hybrid search + guardrails</p>',
            unsafe_allow_html=True)
st.markdown('<div class="hd-div"></div>', unsafe_allow_html=True)

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

# pending_question: вопрос ожидает ответа (стрим идёт после рендера истории)
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ---------- Сайдбар ----------
n_chunks = len(pipe.retriever.docs)
st.sidebar.markdown('<div class="sb-sep"></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sb-title">Index</div>', unsafe_allow_html=True)
st.sidebar.markdown(
    f'<div class="sb-meta">{n_chunks} častí<br>Hybrid search + BM25 + rerank<br>Guardrails: relevance</div>',
    unsafe_allow_html=True)

if llm_ok:
    st.sidebar.markdown(
        '<span class="chip chip-on"><span class="chip-dot"></span>AI odpovede: ON</span>',
        unsafe_allow_html=True)
else:
    st.sidebar.markdown(
        '<span class="chip chip-off"><span class="chip-dot"></span>AI odpovede: OFF</span>',
        unsafe_allow_html=True)

st.sidebar.markdown('<div class="sb-sep"></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sb-label">Pridať dokument (.md / .txt)</div>',
                    unsafe_allow_html=True)
uploaded = st.sidebar.file_uploader("Nahrať dokument", type=["md", "txt"],
                                    label_visibility="collapsed")
if uploaded is not None and uploaded.name not in os.listdir(DOC_DIR):
    with st.spinner("Idxujem..."):
        safe_name = os.path.basename(uploaded.name).replace(" ", "_")
        dest = os.path.join(DOC_DIR, safe_name)
        with open(dest, "wb") as f:
            f.write(uploaded.getbuffer())
        # переиндексация: пересобираем ретривер (подхватит новый док со старыми)
        st.session_state.pipe.retriever = build_retriever()
        st.rerun()

# ---------- Подсказки ----------
examples = [
    "Aká je maximálna teplota reflow?",                    # manuál-smt-montáž → 245 °C
    "Aká je presnosť osadzovacieho stroja?",               # proces-osadzovanie-smt → ±0,05 mm
    "Aké sú skladovacie podmienky spájkovacej pasty?",     # sklad-parametre → 2–10 °C, 24 h
    "Po koľkých doskách sa čistí dno šablóny?",            # pracovny-pokyn-tlac → po 25
    "Aký je interval generálnej údržby stroja?",           # pokyn-udrzba-strojov → 5000 h
    "Ktorý zamestnanec dostal najvyšší plat?",             # off-topic → guardrail «Neviem»
]

st.sidebar.markdown('<div class="sb-label">Skúste sa opýtať</div>', unsafe_allow_html=True)
for ex in examples:
    if st.sidebar.button(ex, use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": ex})
        st.session_state.pending_question = ex
        st.rerun()

# ---------- Чат: рендер истории ----------
for idx, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"], avatar=avatar_for(m["role"])):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            if m.get("guardrail"):
                st.markdown('<div class="gr-line">Guardrail: nízka relevancia — odpoveď odmietnutá</div>',
                            unsafe_allow_html=True)
            elif m.get("sources"):
                with st.expander(f"Zdroj ({len(m['sources'])}):"):
                    _render_sources(m["sources"], m.get("docs"), uid=f"h{idx}")

# ---------- Чат: стрим ответа на новый вопрос ----------
if st.session_state.pending_question:
    q = st.session_state.pending_question
    st.session_state.pending_question = None  # снимаем, чтобы не зациклиться

    with st.chat_message("assistant", avatar=avatar_for("assistant")):
        buf = st.empty()
        # thinking-индикатор (анимированные точки)
        buf.markdown('<div class="thinking">⋯</div>', unsafe_allow_html=True)

        stream_gen = pipe.query_stream(q)
        acc = ""
        meta = None
        for item in stream_gen:
            if isinstance(item, dict):
                meta = item
                break
            acc += item
            buf.markdown(acc)

        if meta is None:
            meta = {"guardrail": False, "sources": [], "ok": True}

        final_answer = meta.get("answer") or acc
        buf.markdown(final_answer)

        # метаданные под ответом
        if meta.get("guardrail"):
            st.markdown('<div class="gr-line">Guardrail: nízka relevancia — odpoveď odmietnutá</div>',
                        unsafe_allow_html=True)
        elif meta.get("sources"):
            with st.expander(f"Zdroj ({len(meta['sources'])}):"):
                _render_sources(meta["sources"], meta.get("docs"), uid="live")

    # сохраняем в историю, не вызываем rerun — всё уже отрендерено
    st.session_state.messages.append({
        "role": "assistant",
        "content": final_answer,
        "guardrail": bool(meta.get("guardrail")),
        "sources": meta.get("sources") or [],
        "docs": meta.get("docs") or [],
        "ok": meta.get("ok", True),
    })

# ---------- Чат: ввод ----------
prompt = st.chat_input("Napíšte otázku k technickej dokumentácii...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.pending_question = prompt
    st.rerun()

# ---------- Чат: сброс ----------
if st.session_state.messages:
    if st.sidebar.button("Vymazať chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------- Превью документа (по клику на источник) ----------
open_doc = st.session_state.get("open_doc")
if open_doc:
    doc_text = _read_doc_text(open_doc)
    st.markdown('<div class="hd-div"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="doc-title">📄 {open_doc}</div>',
                unsafe_allow_html=True)
    st.markdown(
        f'<div class="doc-preview">{doc_text}</div>',
        unsafe_allow_html=True)
    if st.button("Zavrieť dokument", use_container_width=False):
        st.session_state.open_doc = None
        st.rerun()