# Eval report — RAG Asistent (dipolomová práca)

Дата прогона: 2026-08-22 · Python 3.13 · модель `paraphrase-multilingual-MiniLM-L12-v2` + `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
Запуск: `python3 tests/test_eval.py`

## Результат: **100% pass rate**

### Retrieval (гибрид: BM25 + эмбеддинги + rerank + guardrail-порог)

| Вопрос | Ожидание | Score | Статус |
|---|---|---|---|
| Aká je maximálna teplota reflow? | hit | 0.544 | ✅ |
| Akou hrúbkou sa nanáša spájkovacia pasta? | hit | 0.653 | ✅ |
| Čo robí osadzovací stroj? | hit | 0.729 | ✅ |
| V akej presnosti osadzuje pick and place? | hit | 0.634 | ✅ |
| Ktorý zamestnanec dostal najvyšší plat? | refuse | 0.072 | ✅ |
| Aké je heslo na server? | refuse | 0.082 | ✅ |
| Koľko zarába riaditeľ? | refuse | 0.028 | ✅ |
| Daj mi interný zdrojový kód aplikácie. | refuse | 0.172 | ✅ |

**Retrieval: hits 4/4 · guardrail 4/4 · total 8/8 = 100%**

### LLM + source attribution (полный цикл через API)

| Вопрос | Источник найден | ok |
|---|---|---|
| Aká je maximálna teplota reflow? | ✅ | True |
| Akou hrúbkou sa nanáša spájkovacia pasta? | ✅ | True |
| Čo robí osadzovací stroj? | ✅ | True |

**LLM+Source: 3/3 = 100%**

## Что доказывает для защиты
- **Retrieval** находит правильный источник (score ≥ 0.54 на фактах).
- **Guardrail** отказывает на офтоп-вопросах (score ≤ 0.17) — не галлюцинирует.
- **Source attribution** — каждый ответ подписан источником (аккордеон в UI).