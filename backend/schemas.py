from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    active_tab: str | None = None
    chart_id: str | None = None
    selected_year: int | None = None
    compare_year: int | None = None
    top_k: int = Field(default=4, ge=1, le=8)
    conversation: list[ChatTurn] = Field(default_factory=list)


class Citation(BaseModel):
    label: str
    title: str
    source: str
    snippet: str
    kind: str
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    exact_facts: list[str] = Field(default_factory=list)
    retrieval_backend: str
    model: str | None = None


class SubstitutionPreviewResponse(BaseModel):
    verdict_title: str
    verdict_body: str
    verdict_level: Literal["positive", "warning", "negative", "neutral"]
    hs8542_actual: float | None = None
    hs3818_actual: float | None = None
    hs8542_delta: float | None = None
    hs3818_delta: float | None = None
