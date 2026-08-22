# -*- coding: utf-8 -*-
"""
Retrieval: hybrid search (vector + BM25) + RRF fusion + cross-encoder rerank.

Это «самая умная» часть пайплайна и главный козырь диплома:
- векторный поиск ловит смысл (montáž ložiska == замена подшипника);
- BM25 ловит точные термины/номера (IP65, 245 °C, 0402);
- RRF сливает оба ранжирования;
- cross-encoder переранжирует топ-кандидатов (пары вопрос+чанк целиком).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from rank_bm25 import BM25Okapi

# Стоп-слова (словацкие + общий boilerplate), чтобы BM25 не хватал
# одинаковые вступительные фразы и не раздувал ложные совпадения.
STOPWORDS = {
    "a", "v", "sa", "na", "je", "že", "ktoré", "ktorý", "o", "so", "po",
    "do", "pred", "pre", "pod", "nad", "ale", "ako", "alebo", "od", "zo",
    "pri", "z", "s", "k", "u", "i", "aj", "tento", "táto", "tieto",
    # boilerplate демо-доков
    "dokument", "popisuje", "štandardné", "výrobné", "postupy", "používané",
    "výrobných", "cieľom", "zabezpečiť", "opakovateľnú", "zhode", "predpis",
    "linke", "dosiek", "plošných", "spojov", "profil", "parametre", "kľúčové",
    "hodnoty", "nasledujúce", "pre", "dodržanie", "kvality", "kontrolné",
    "body", "orientačné", "štandardný", "proces", "platia", "výrobný",
}

# Лучше не хардкодить английский токенизатор, но для запросов «смешанных»
# ключевых слов (SMT, AOI, QMS) пропускаем:
TOKEN_KEEP = {"smt", "aoi", "qms", "rgb", "ips", "plc", "snagcu", "sac305",
              "0402", "0805", "0603", "ip65", "iwe"}


def default_tokenize(text: str):
    """Токенизация для BM25: нижний регистр, только слова ≥2 симв.",
    убираем стоп-слова и числа-референсы не трогаем."""
    import re
    words = re.findall(r"[a-záéíóúýčďťňľščžů]+|\d+[\d,\.\-]*°?[c]?", text.lower())
    out = []
    for w in words:
        if w in TOKEN_KEEP:
            out.append(w)
        elif len(w) >= 3 and w not in STOPWORDS:
            out.append(w)
    return out


@dataclass
class Doc:
    """Один чанк документа."""
    text: str
    source: str        # имя файла/страница
    doc_id: str
    chunk_id: int


class HybridRetriever:
    """Держит эмбеддинги + BM25 индекс в памяти (для демо достаточно)."""

    MIN_RELEVANCE = 0.35        # порог guardrail: ниже → «Neviem»
    TOP_CANDIDATES = 10         # сколько берём после fusion
    TOP_FINAL = 3               # сколько отдаём после rerank

    def __init__(self, embedder, reranker=None, tokenizer_fn=None):
        self.embedder = embedder
        self.reranker = reranker
        self.tokenizer_fn = tokenizer_fn or default_tokenize
        self.docs: List[Doc] = []
        self.vectors: Optional[np.ndarray] = None
        self.bm25: Optional[BM25Okapi] = None

    # ---------- INGEST ----------
    def add_docs(self, docs: List[Doc]):
        if not docs:
            return
        self.docs.extend(docs)
        # пересчитываем все векторы и BM25 (демо: индексируем заново)
        texts = [d.text for d in self.docs]
        self.vectors = self.embedder.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True
        ).astype(np.float32)
        tokenized = [self.tokenizer_fn(t) for t in texts]
        self.bm25 = BM25Okapi(tokenized)

    # ---------- SEARCH ----------
    def _bm25_scores(self, query: str) -> np.ndarray:
        scores = self.bm25.get_scores(self.tokenizer_fn(query))
        # нормализуем BM25 в [0,1] (min-max) — иначе несопоставимо с косинусом
        lo, hi = scores.min(), scores.max()
        if hi - lo < 1e-9:
            return np.zeros_like(scores)
        return (scores - lo) / (hi - lo)

    def _vector_scores(self, query: str) -> np.ndarray:
        q = self.embedder.encode(
            [query], normalize_embeddings=True, convert_to_numpy=True
        ).astype(np.float32)[0]
        return (self.vectors @ q).astype(float)   # косинус (нормализован)

    def search(self, query: str, hyb_w=0.5) -> List[tuple]:
        """Возвращает [ (score, Doc), ... ] после fusion, до rerank."""
        if not self.docs:
            return []
        vec = self._vector_scores(query)          # похожесть [0..1]
        bm25 = self._bm25_scores(query)           # нормализованные BM25
        # RRF-подобная комбинация: взвешенная сумма + доли топов
        # простая и устойчивая: линейная смесь нормализованных оценок
        blended = hyb_w * vec + (1 - hyb_w) * bm25
        order = np.argsort(-blended)[: self.TOP_CANDIDATES]
        return [(float(blended[i]), self.docs[i]) for i in order]

    def retrieve(self, query: str,
                 hyb_w: float = 0.5,
                 rerank: bool = True,
                 use_guardrail: bool = True) -> dict:
        """
        Полный путь: fusion -> rerank -> guardrail.
        Guardrail-порог применяется к HYBRID-скору (совместимому с порогом),
        rerank лишь упорядочивает кандидатов (его скор несопоставим).
        Возвращает dict для LLM/UI: {ok, score, answer_docs, refuse}
        """
        cand = self.search(query, hyb_w)   # [(hybrid_score, Doc), ...]
        if not cand:
            return {"ok": False, "reason": "no_index", "docs": [], "score": 0.0}

        if rerank and self.reranker and len(cand) > 1:
            # cross-encoder: сортируем кандидатов по CE-скору
            pairs = [(query, d.text) for _, d in cand]
            ce = self.reranker.predict(pairs, show_progress_bar=False).tolist()
            ranked = sorted(zip(ce, cand), key=lambda x: -x[0])
            final = ranked[: self.TOP_FINAL]        # [(ce, (hybrid, Doc))]
            # guardrail решает по максимальному hybrid-скору СРЕДИ ВСЕХ
            # кандидатов (есть ли вообще релевантный материал), а не топ-CE.
            best_hybrid = max(h for h, _ in cand)
            docs_out = [d for (_, (_, d)) in final]
        else:
            final_sorted = sorted(cand, key=lambda x: -x[0])
            final = final_sorted[: self.TOP_FINAL]  # [(hybrid, Doc)]
            best_hybrid = final[0][0]
            docs_out = [d for _, d in final]

        # GUARDRAIL: порог по hybrid-скору лучшего кандидата
        if use_guardrail and best_hybrid < self.MIN_RELEVANCE:
            return {"ok": False, "reason": "low_relevance",
                    "score": best_hybrid, "docs": docs_out, "refuse": True}
        return {"ok": True, "reason": "ok", "score": best_hybrid,
                "docs": docs_out, "refuse": False}