# React + RAG Setup

This repo now includes a separate React frontend in `frontend/` and a FastAPI + Groq backend in `backend/`.

## 1. Backend env

Create `backend/.env` from `backend/.env.example` and set:

- `GROQ_API_KEY`
- `GROQ_MODEL`
- `VECTOR_STORE=memory` for the zero-setup default
- `VECTOR_STORE=chroma` if you install Chroma and want persisted local retrieval

## 2. Python dependencies

The root `requirements.txt` already includes FastAPI, Groq, pandas, scikit-learn, and uvicorn.

Optional Chroma install:

```bash
pip install -r backend/requirements-rag.txt
```

## 3. Start the backend

```bash
uvicorn backend.app:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The React app runs at `http://127.0.0.1:5173`.

## 5. What the backend does

- Reads `data/processed/*.csv` and `outputs/reports/*`
- Builds dashboard payloads for the React UI
- Builds a retrieval corpus from the policy report, evaluation files, and chart summaries
- Uses Groq for answer generation
- Falls back gracefully if Chroma is not installed

## 6. Retrieval design

- Narrative retrieval comes from report/evaluation text and chart summaries.
- Exact numeric facts come from the processed CSVs and forecast files at request time.
- Synthetic 2025-2026 substitution files remain clearly separated from historical evidence through 2024.
