# RAG Asistent — дипломная работа (RAG + guardrails + hybrid search)

Ассистент для технической документации. Отвечает по документам, найдя
релевантные части **гибридным поиском** (векторный + BM25 + cross-encoder
rerank) и защищаясь **guardrails** (порог релевантности → «Neviem» + атрибуция
источника).

> Демо-данные: 8 словацких тех. процедур по SMT-монтажу (папка `docs/`).
> Если хочешь на реальных документах TESLA — просто положи .md/.pdf в `docs/`
> и перезапусти (см. «Как заменить документы»).

---

## 1. Установка (Windows, Python 3.10+)

```bat
:: 1) создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate

:: 2) поставить зависимости
pip install -r requirements.txt
```

> Примечание по Windows: `requirements.txt` включает CPU-сборку `torch`.
> Если `pip install` ругнётся на `torch==x+cpu`, поставь обычный
> `pip install torch` (процессорная версия подхватится сама).

## 2. Ключ OpenRouter (для ответов LLM)

Создай файл `.env` рядом с проектом (скопируй из `.env.example`):

```
OPENROUTER_API_KEY=sk-or-v1-xxxx
```

Без ключа ассистент всё равно работает — в режиме **поиска без LLM**
(показывает найденные части и оценку). С ключом — даёт текстовый ответ.

## 3. Запуск UI

```bat
.venv\Scripts\activate
streamlit run app.py
```

Открой `http://localhost:8501`. Вопросы для проверки:

| Вопрос | Ожидание |
|---|---|
| `Aká je maximálna teplota reflow?` | ответ + «Zdroj: manuál-smt-montáž.md» |
| `Čo robí osadzovací stroj?` | ответ + источник |
| `Aké je heslo na server?` | 🛡️ **Neviem** (guardrail) |
| `Koľko zarába riaditeľ?` | 🛡️ **Neviem** (guardrail) |

## 4. Тесты (проверка качества)

```bat
.venv\Scripts\activate
python tests/test_eval.py      :: eval: 4/4 точных + 4/4 guardrail (pass-rate 100%)
python tests/full_cycle.py     :: полный цикл с реальным LLM-ответом и источником
python tests/smoke.py          :: быстрый smoke
```

## 5. Как заменить документы

1. Положи свои `.md` / `.pdf` в папку `docs/` (старые — удали/переименуй).
2. Перезапусти приложение — индекс пересоберётся при старте.
   (PDF → текст: `src/ingest.py` умеет markdown; PDF-парсер подключается
   при наличии `pymupdf`. Для диплома добавляй по мере надобности.)

## Структура

```
app.py               Streamlit UI
src/
  ingest.py          документы → чанки → векторный + BM25 индексы
  retrieval.py       hybrid search (RRF fusion) + cross-encoder rerank
  guardrails.py      порог релевантности + «Neviem» + атрибуция
  llm.py             LLM-клиент OpenRouter (fallback-цепочка)
  pipeline.py        весь цикл вопрос → ответ
  make_demo_docs.py  генератор демо-документов (не обязателен)
tests/               eval + полный цикл + smoke
docs/                демо-документы (SMT)
```

## Идеи на развитие (для диплома — step beyond)

- Настоящий бенчмарк: собери 30–50 вопросов от инженеров + разметку ответов,
  считай precision/recall/F1 против baseline'ов (BM25-only, vector-only).
- Guardrail второго уровня — калибровка уверенности, а не только порог.
- Чанкинг под структуру: таблицы/схемы не резать, термины не рвать.