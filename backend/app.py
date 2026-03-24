from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import sys

# Support running Uvicorn from either the repo root or the backend directory.
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import ChatRequest, ChatResponse, SubstitutionPreviewResponse
from backend.services.chat_service import ChatService
from backend.services.dashboard_service import DashboardService
from backend.services.rag_service import RetrievalService
from backend.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    dashboard = DashboardService(settings)
    retrieval = RetrievalService(settings)
    chat = ChatService(settings, dashboard, retrieval)
    app.state.dashboard = dashboard
    app.state.retrieval = retrieval
    app.state.chat = chat
    yield


app = FastAPI(
    title="SemiTrack RAG API",
    version="0.1.0",
    summary="React + Groq + local retrieval backend for the SemiTrack dashboard",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "vector_store": settings.vector_store}


@app.get("/api/dashboard")
def dashboard() -> dict:
    return app.state.dashboard.get_dashboard_payload()


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return app.state.chat.answer(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/substitution/preview", response_model=SubstitutionPreviewResponse)
async def substitution_preview(file: UploadFile = File(...)) -> SubstitutionPreviewResponse:
    try:
        contents = await file.read()
        return app.state.dashboard.parse_substitution_upload(contents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not parse uploaded CSV: {exc}") from exc
