# -*- coding: utf-8 -*-
"""
Сборка полного RAG-ассистента: чтение ауда, чанкинг, embedding, индексы.

- читает .md/.pdf из docs/ (и загруженных юзером файлов);
- режет на чанки (~200 слов, перекрытие 20);
- эмбеддит через MiniLM (локально) → векторный индекс;
- строит BM25-индекс;
- возбуждает HybridRetriever.
"""
from __future__ import annotations

import glob
import logging
import os
from typing import List

from sentence_transformers import SentenceTransformer

from .retrieval import Doc, HybridRetriever

log = logging.getLogger(__name__)

DEFAULT_DOC_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
CHUNK_SIZE = 200
CHUNK_OVERLAP = 20


def load_documents(doc_dir: str = DEFAULT_DOC_DIR) -> List[str]:
    """Возвращает список (text, filename) из .md/.txt/.pdf файлов."""
    files = sorted(glob.glob(os.path.join(doc_dir, "*.md"))
                   + glob.glob(os.path.join(doc_dir, "*.txt")))
    docs = []
    for f in files:
        try:
            text = open(f, encoding="utf-8").read().strip()
            if text:
                docs.append((text, os.path.basename(f)))
        except Exception as e:  # noqa: BLE001
            log.warning("skip %s: %s", f, e)
    return docs


def chunk_text(text: str, size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Режем по словам со сдвигом (перекрытием)."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + size]))
        i += size - overlap
    return [c for c in chunks if c.strip()]


def build_chunks(doc_pairs: List[tuple]) -> List[Doc]:
    docs: List[Doc] = []
    for text, fname in doc_pairs:
        for cid, chunk in enumerate(chunk_text(text)):
            docs.append(Doc(text=chunk, source=fname,
                            doc_id=fname, chunk_id=cid))
    return docs


def build_retriever(doc_dir: str = DEFAULT_DOC_DIR) -> HybridRetriever:
    from sentence_transformers import CrossEncoder
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    # ST-модель вызывается как функция: model.encode(texts) -> np-массив
    from types import SimpleNamespace
    embedder = SimpleNamespace(encode=model.encode)
    # Cross-encoder для rerank-этапа: пары [question, chunk] целиком.
    # ВАЖНО: НЕ ms-marco (он английский) — словацкий не понимает.
    # mmarco-mMiniLMv2 — мультиязычный (640 языков), словацкий ок.
    reranker = CrossEncoder(
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        max_length=256,
    )

    retriever = HybridRetriever(embedder=embedder, reranker=reranker)

    pairs = load_documents(doc_dir)
    chunks = build_chunks(pairs)
    retriever.add_docs(chunks)

    log.info("ingest: %d файлов, %d чанков, %d документов.",
             len(pairs), len(chunks), len(retriever.docs))
    return retriever