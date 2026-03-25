# SemiTrack India

SemiTrack India is a React + FastAPI dashboard for analyzing India's semiconductor import dependence, supplier concentration, and substitution signals across HS 8542 and HS 3818.

The live app now uses:

- `frontend/`: Vite + React dashboard UI
- `backend/`: FastAPI API, dashboard assembly, RAG retrieval, and chat orchestration
- `data/`: committed historical and synthetic CSV inputs
- `outputs/reports/`: runtime report artifacts that the RAG layer reads at runtime

The old monolithic Streamlit/Gradio prototype has been removed. For the full retrieval architecture and RAG internals, read [`RAG_SETUP.md`](./RAG_SETUP.md).

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

This single `requirements.txt` now covers both:

- the React + FastAPI app runtime
- the scientific Python stack used by the project notebooks

`ipykernel` is intentionally not included. If you want to open the `.ipynb` files in a notebook UI, install your preferred Jupyter tooling separately in your own environment.

### 2. Configure the backend

Copy `backend/.env.example` to `backend/.env` and set values as needed.

Important variables:

- `GROQ_API_KEY`: optional; enables model-generated answers
- `GROQ_MODEL`: Groq model name
- `VECTOR_STORE=memory`: zero-setup default and recommended local mode
- `VECTOR_STORE=chroma`: optional persisted local retrieval if you also install `backend/requirements-rag.txt`
- `CORS_ORIGINS`: comma-separated frontend origins

### 3. Start the backend

```bash
uvicorn backend.app:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The React app will be available at `http://127.0.0.1:5173`.

## What Runs In Production

The production web app consists of:

- `GET /api/health`: lightweight health check
- `GET /api/dashboard`: dashboard payload assembled from committed CSV/report files
- `POST /api/chat`: RAG-backed chat with optional Groq generation
- `POST /api/substitution/preview`: in-memory CSV upload parser for substitution checks

You do not need:

- Streamlit
- Gradio
- a database
- a hosted vector database

By default, retrieval uses an in-memory hashing-based vector representation built at startup.

## Data Used At Runtime

The current backend reads from:

- `data/processed/india_semiconductor_integrated_annual.csv`
- `data/processed/india_semiconductor_country_year_breakdown.csv`
- `data/synthetic/actual_imports_2025_2026.csv`
- `outputs/reports/arimax_forecast_values.csv`
- `outputs/reports/arimax_evaluation.txt`
- `outputs/reports/india_semiconductor_policy_report.md`
- `outputs/reports/model_evaluation.csv`
- `outputs/reports/stationarity_report.txt`
- `outputs/reports/mixshift_report.txt`

That means the app is file-backed and can run without a database bootstrap. If `outputs/reports/` is missing in your clone, regenerate those files through the notebook workflow before starting the backend.

## Notebook Workflow

The notebooks remain available for the analysis workflow:

```bash
python run_pipeline.py
```

That script prints the recommended notebook order and the key output folders.

## Deployment Direction

For the current split-stack app:

- frontend: static hosting such as Vercel
- backend: Python web service such as Render

Set `VITE_API_BASE_URL` in the frontend and `CORS_ORIGINS` in the backend to the final public URLs.
