# RAG Setup

This document explains the retrieval-augmented generation architecture used by the current React + FastAPI version of SemiTrack India. It is written as a systems note, not just a quick-start guide, so that someone new to the repo can understand what data is loaded, what gets embedded, what stays outside retrieval, and how a chat request turns into an answer.

## 1. Why RAG Exists In This Project

The dashboard needs to answer two kinds of questions:

- exact questions such as "what was China's share in 2024?" or "compare 2018 and 2024"
- narrative questions such as "why does the dashboard say there is no substitution yet?" or "what does this chart imply?"

A plain LLM is weak at the first category because it can hallucinate numbers. A plain dashboard is weak at the second category because it can show charts but not synthesize them conversationally.

So this repo uses a mixed design:

- exact numeric facts are computed directly from committed CSV/report artifacts at request time
- narrative context is retrieved from a small local corpus made from policy/report text and chart summaries
- the final answer is generated either by Groq or, if no API key is configured, by a deterministic fallback path

This is intentionally a lightweight RAG stack. It does not require a hosted vector database or an external embedding API.

## 2. High-Level Architecture

The current runtime is split into two app layers:

- `frontend/`: React dashboard, chart views, upload flow, and chat panel
- `backend/`: FastAPI API, dashboard assembly, retrieval, exact-fact generation, and chat orchestration

The main backend pieces are:

- `backend/app.py`: API entrypoint and lifespan wiring
- `backend/settings.py`: file paths and environment-driven settings
- `backend/services/dashboard_service.py`: loads CSV/report artifacts and builds the dashboard payload
- `backend/services/rag_service.py`: builds documents, embeddings, and retrieval results
- `backend/services/chat_service.py`: enriches the query, combines exact facts with retrieved context, and calls Groq when configured
- `backend/rag/chart_catalog.py`: hand-authored chart descriptions that make the charts retrievable as text

## 3. What Data Is Loaded At Runtime

The web app is file-backed. It does not query a database.

### Historical structured data

These CSV files are loaded by `DashboardService`:

- `data/processed/india_semiconductor_integrated_annual.csv`
  Contains the yearly historical series used for overview, import analysis, year analysis, and many exact facts.

- `data/processed/india_semiconductor_country_year_breakdown.csv`
  Contains per-country, per-year supplier rows used for supplier concentration, risk views, and supplier-specific facts.

- `data/synthetic/actual_imports_2025_2026.csv`
  Provides the default substitution-tracker preview data for future-year simulated comparisons.

- `outputs/reports/arimax_forecast_values.csv`
  Provides the BAU forecast that the overview trajectory and substitution tracker rely on.

### Narrative report artifacts

These report files are turned into retrieval documents:

- `outputs/reports/india_semiconductor_policy_report.md`
- `outputs/reports/arimax_evaluation.txt`
- `outputs/reports/stationarity_report.txt`
- `outputs/reports/mixshift_report.txt`
- `outputs/reports/model_evaluation.csv` is used by the dashboard layer for exact context, but the text-heavy reports matter more for retrieval

### Hand-authored chart knowledge

`backend/rag/chart_catalog.py` defines text summaries for the charts. These are important because a chart image itself is not embedded. Instead, we make each chart retrievable by storing:

- chart title
- tab association
- human summary
- source-file hints

This gives the assistant language it can retrieve when the user asks about "the risk corridor", "the year context chart", or another UI element.

## 4. What Gets Stored In The Retrieval Corpus

The retrieval corpus is built at backend startup by `RetrievalService`.

It contains three families of documents:

### A. Markdown policy report sections

The policy report markdown file is split by headings. Each heading section becomes one or more retrieval documents. The heading is preserved as the document title so retrieval results keep some semantic structure instead of becoming anonymous blobs.

### B. Plain-text evaluation and report chunks

Text reports like stationarity, ARIMAX evaluation, and mix-shift notes are chunked into short text windows and stored as retrieval documents.

### C. Chart catalog entries

Every chart in `chart_catalog.py` becomes a retrieval document even though the chart itself is rendered from structured JSON in the frontend. This is what lets the assistant explain chart meaning in natural language.

## 5. What Does Not Go Into The Vector Store

This is a key design choice.

The following information is not embedded as free-text documents by default:

- raw yearly CSV rows
- country table rows
- per-year exact import values
- compare-mode deltas
- synthetic verdict math

Instead, those are computed live by `DashboardService.build_exact_facts(...)`.

That separation exists because structured tabular facts are better computed directly than retrieved fuzzily. Retrieval is for narrative context; direct computation is for authoritative numbers.

## 6. How Embeddings Work

This project does not call an external embedding API.

Instead, `backend/services/rag_service.py` uses `sklearn.feature_extraction.text.HashingVectorizer` through a thin wrapper called `HashingEmbedder`.

Important characteristics of the current embedder:

- feature size: `2048`
- n-grams: `(1, 2)`
- `alternate_sign=False`
- `norm="l2"`

What that means in practice:

- text is turned into a fixed-size sparse vector using hashed token features
- both unigrams and bigrams contribute, which helps with phrases like "China share" or "structural break"
- L2 normalization makes dot-product similarity behave like cosine-style similarity

This is not a semantic embedding model in the large-LLM sense. It is a lightweight lexical vectorizer. That is acceptable here because:

- the corpus is small
- the domain vocabulary is narrow and repetitive
- many useful questions reuse project-specific words like `ARIMAX`, `HHI`, `substitution`, `China share`, `supplier risk`, and chart names

## 7. Vector Store Options

There are two retrieval backends:

### Default: `memory`

The default path stores vectors in memory only. At startup:

1. documents are built
2. each document is hashed into a vector
3. a matrix of document vectors is kept in RAM
4. query search is a vector dot product against that matrix

This is the recommended mode for local development and low-friction deployment.

### Optional: `chroma`

If `VECTOR_STORE=chroma` and `chromadb` is installed from `backend/requirements-rag.txt`, the app uses a local Chroma persistent client. This is still local to the machine; it is not a hosted vector DB.

The code currently rebuilds the `semichat` collection at startup, so Chroma here is mainly a pluggable local store rather than a long-lived offline indexing pipeline.

## 8. Chunking Strategy

Chunking is intentionally simple and readable.

### Markdown chunking

For the markdown policy report:

- split on `##` and `###` headings
- keep the heading as the document title
- further split large sections into overlapping chunks

### Plain-text chunking

For text reports:

- whitespace is normalized
- target chunk size is about `900` characters
- overlap is about `120` characters
- if possible, chunks end near sentence boundaries

This keeps snippets short enough to cite in the UI while still retaining enough local context for generation.

## 9. How A Chat Request Actually Works

When the user sends a chat message from the React app, the following happens:

### Step 1. Frontend sends UI context

The chat payload includes more than the question. The frontend also sends:

- `active_tab`
- `chart_id`
- `selected_year`
- `compare_year`
- recent conversation turns

This matters because a question like "why is this high?" is meaningless without knowing which tab or chart is active.

### Step 2. Backend builds exact facts

`ChatService` first asks `DashboardService.build_exact_facts(...)` for structured facts tied to:

- explicitly mentioned years in the question
- selected and compare years from the UI
- supplier names in the question
- substitution-related triggers

This can produce statements like:

- the 2024 import bill
- China share and HHI values
- year-to-year deltas
- supplier snapshots
- substitution diagnostics
- forecast lines for future years

These are authoritative because they are computed directly from the app's loaded data rather than guessed from retrieved prose.

### Step 3. Backend builds a richer retrieval query

The retrieval query is not just the raw question. `ChatService._build_query(...)` appends useful hints such as:

- active tab
- chart title and summary
- selected and compare year
- detected comparison context
- a short compare summary when compare mode is active

This is a major RAG improvement over a naive "embed the user question only" approach.

### Step 4. Retrieval runs over the local corpus

`RetrievalService.search(...)` returns the top matching documents. `ChatService` then:

- deduplicates them
- keeps a candidate pool slightly larger than the final `top_k`
- applies a score threshold so very weak matches are dropped unless they are among the strongest initial results

This helps stop the answer from being cluttered with barely relevant text chunks.

### Step 5. Citations are built

Retrieved documents are converted into UI citations containing:

- short label like `C1`
- title
- source file or source type
- snippet
- kind
- score

These citations are shown separately in the chat panel.

### Step 6. Generation happens, or fallback happens

If `GROQ_API_KEY` is set:

- the backend sends a system prompt plus question, exact facts, retrieved context, and recent conversation to Groq
- the answer is cleaned before returning to the frontend

If `GROQ_API_KEY` is not set:

- the backend falls back to a deterministic answer built from exact facts and attached citations

This means the app still works without a paid or configured LLM key, just with less fluent prose.

## 10. Why Exact Facts And Retrieval Are Combined

This is the heart of the implementation.

If we used retrieval alone:

- numeric answers could be stale, approximate, or missing
- compare-mode questions would be weak
- supplier-specific facts would depend on whether a report happened to mention them

If we used exact computation alone:

- the assistant would know numbers but not how to explain report conclusions
- chart interpretation would sound mechanical
- longer narrative answers would become hardcoded and brittle

So the project uses a hybrid answer stack:

- exact facts for precision
- retrieval for narrative support
- LLM generation for fluent synthesis

## 11. What Changed When We Moved To RAG

Before the current architecture, the repo had a monolithic prototype UI path. The RAG-enabled React version changed the system in several important ways.

### A. Frontend and backend were separated

Instead of a single prototype UI file, the app now has:

- a dedicated React frontend for dashboard rendering and chat UX
- a dedicated FastAPI backend for data loading and RAG orchestration

This makes the app deployable as a standard web stack.

### B. Dashboard logic moved into services

The data assembly logic now lives in `DashboardService`, which:

- loads the structured datasets once
- derives chart-ready series and KPI payloads
- computes exact year and comparison facts
- parses upload CSVs for the substitution preview

That decomposition is what made RAG integration manageable. The chat layer can ask the dashboard layer for precise facts instead of re-implementing business logic.

### C. Text knowledge was formalized into a retrieval corpus

We introduced:

- report chunking
- chart text descriptors
- retrieval documents with titles and source metadata

This turned the project from "dashboard plus model API" into "dashboard plus retrievable domain memory".

### D. The query became UI-aware

The frontend now sends chart and tab context, and the backend folds that into retrieval. This is one of the most practical changes: the same text question can mean different things depending on which chart the user is looking at.

### E. The app gained a no-key fallback path

The chat system is resilient:

- with Groq configured, users get fluent generated answers
- without Groq, users still get deterministic facts and supporting citations

That was an important product change because it keeps the system usable even when model credentials are unavailable.

## 12. What The RAG Layer Does Not Do

The current RAG implementation is intentionally scoped.

It does not:

- index raw chart images
- run OCR
- retrieve from the internet
- persist user conversations in a database
- learn from uploaded CSVs beyond the current preview request
- build long-term semantic embeddings with a hosted model

This keeps the system cheap and easy to deploy, but it also defines the current limits.

## 13. Substitution Tracker And RAG

The substitution tracker is mostly not a retrieval problem.

Its verdict is computed directly from uploaded CSV values and baseline BAU expectations. RAG helps only on the explanation side, for example when a user asks what substitution means historically or why a given divergence matters.

So in this project:

- substitution verdict math is deterministic
- substitution interpretation can be retrieval-supported

That division is deliberate and good design.

## 14. Environment Variables

Current backend settings are:

- `GROQ_API_KEY`
- `GROQ_MODEL`
- `VECTOR_STORE`
- `CHROMA_DIR`
- `CORS_ORIGINS`

Recommended defaults:

- `VECTOR_STORE=memory`
- `GROQ_MODEL=llama-3.3-70b-versatile`

Use `chroma` only if you specifically want the optional local persistent store.

## 15. Operational Notes

### Startup cost

At backend startup, the app:

- loads structured CSVs
- loads report text
- builds retrieval documents
- builds the in-memory vector matrix

Because the corpus is small, this remains lightweight enough for normal web deployment.

### Deployment implications

Since the app reads committed files and does not require a database:

- deployment is simpler
- reproducibility is higher
- the main runtime risk becomes missing files or missing env vars, not infrastructure complexity

### Why local file-backed retrieval is enough here

The corpus is small and domain-specific. A hosted vector DB would add cost and complexity without clear benefit at the current scale.

## 16. If You Want To Extend The RAG Later

Good next improvements would be:

- add richer chart-specific retrieval text where explanations are still thin
- include structured table summaries for more supplier-level natural language coverage
- add evaluation tests for retrieval quality on representative domain questions
- add a prebuilt indexing command if the corpus grows much larger
- optionally swap the hashing embedder for a stronger embedding model once scale or query diversity demands it

## 17. Mental Model In One Paragraph

SemiTrack's RAG is a hybrid assistant layered on top of a deterministic dashboard. The dashboard owns truth for numbers, years, comparisons, and substitution verdicts. The retrieval layer owns narrative memory from reports and chart descriptions. The LLM, when enabled, sits on top of those two sources and turns them into concise explanations. That separation is the core design choice and the main reason the current system is both practical and trustworthy.
