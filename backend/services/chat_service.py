from __future__ import annotations

import re

from groq import Groq

from backend.schemas import ChatRequest, ChatResponse, Citation
from backend.services.dashboard_service import DashboardService
from backend.services.rag_service import RetrievalService, SourceDocument
from backend.settings import Settings


class ChatService:
    def __init__(self, settings: Settings, dashboard: DashboardService, retrieval: RetrievalService) -> None:
        self.settings = settings
        self.dashboard = dashboard
        self.retrieval = retrieval
        self._client: Groq | None = None

    def answer(self, request: ChatRequest) -> ChatResponse:
        exact_facts = self.dashboard.build_exact_facts(
            request.question,
            request.selected_year,
            request.compare_year,
        )
        candidate_k = min(max(request.top_k + 2, 4), 8)
        retrieved = self._select_documents(
            self.retrieval.search(self._build_query(request), top_k=candidate_k),
            limit=request.top_k,
        )
        citations = self._build_citations(retrieved)

        if not self.settings.groq_api_key:
            return ChatResponse(
                answer=self._fallback_answer(exact_facts, citations),
                citations=citations,
                exact_facts=exact_facts,
                retrieval_backend=self.retrieval.backend_name,
                model=None,
            )

        try:
            answer = self._generate_answer(request, exact_facts, citations)
            model = self.settings.groq_model
        except Exception:
            answer = self._fallback_answer(exact_facts, citations)
            model = None
        return ChatResponse(
            answer=answer,
            citations=citations,
            exact_facts=exact_facts,
            retrieval_backend=self.retrieval.backend_name,
            model=model,
        )

    def _build_query(self, request: ChatRequest) -> str:
        parts = [request.question]
        explicit_years = self._extract_years(request.question)
        question_lower = request.question.lower()
        compare_requested = any(token in question_lower for token in ("compare", "versus", " vs ", "difference", "between"))
        should_use_active_pair = (
            request.selected_year
            and request.compare_year
            and request.compare_year != request.selected_year
            and (
                not explicit_years
                or (compare_requested and (request.selected_year in explicit_years or request.compare_year in explicit_years))
            )
        )
        if request.active_tab:
            parts.append(f"Tab: {request.active_tab}")
        chart = self.dashboard.get_chart_context(request.chart_id)
        if chart:
            parts.append(f"Chart: {chart['title']}. {chart['summary']}")

        if explicit_years:
            parts.append(f"Question years: {', '.join(str(year) for year in sorted(explicit_years))}")
        else:
            if request.selected_year and not should_use_active_pair:
                parts.append(f"Selected year: {request.selected_year}")
            if request.compare_year and request.compare_year != request.selected_year and not should_use_active_pair:
                parts.append(f"Compare year: {request.compare_year}")
        if should_use_active_pair:
            parts.append(f"Selected year: {request.selected_year}")
            parts.append(f"Compare year: {request.compare_year}")
            comparison = self.dashboard.compare_years(
                min(request.selected_year or request.compare_year, request.compare_year),
                max(request.selected_year or request.compare_year, request.compare_year),
            )
            if comparison:
                parts.append(
                    f"Comparison: {comparison['fromYear']} to {comparison['toYear']}, "
                    f"China share delta {comparison['chinaShareDelta']}, "
                    f"HHI delta {comparison['hhiDelta']}."
                )
        return " | ".join(parts)

    def _select_documents(self, documents: list[SourceDocument], limit: int) -> list[SourceDocument]:
        unique: list[SourceDocument] = []
        seen: set[str] = set()
        for document in documents:
            if document.doc_id in seen:
                continue
            seen.add(document.doc_id)
            unique.append(document)

        if not unique:
            return []

        scored = [document.score for document in unique if document.score is not None]
        if not scored:
            return unique[:limit]

        max_score = max(scored)
        threshold = max(0.08, max_score * 0.55)
        filtered: list[SourceDocument] = []
        for index, document in enumerate(unique):
            if index < 2 or document.score is None or document.score >= threshold:
                filtered.append(document)
            if len(filtered) >= limit:
                break
        return filtered

    def _build_citations(self, documents: list[SourceDocument]) -> list[Citation]:
        citations: list[Citation] = []
        for index, document in enumerate(documents, start=1):
            citations.append(
                Citation(
                    label=f"C{index}",
                    title=document.metadata.get("title", "Source"),
                    source=document.metadata.get("source", "local"),
                    snippet=self._trim(document.text, 180),
                    kind=document.metadata.get("kind", "document"),
                    score=document.score,
                )
            )
        return citations

    def _generate_answer(self, request: ChatRequest, exact_facts: list[str], citations: list[Citation]) -> str:
        system_prompt = (
            "You are SemiTrack AI, the assistant for a semiconductor import dashboard. "
            "Use only the provided context. Exact facts are authoritative CSV-derived values and should override "
            "more general retrieved text when they directly answer the question. "
            "Answer the question directly in the first sentence, then explain why with the smallest amount of detail "
            "needed to be useful. Default to one short conclusion paragraph plus up to three flat bullets or one short "
            "follow-up paragraph. Avoid markdown headings, tables, and separate Sources sections unless the user explicitly "
            "asks for them. Use inline citation labels like [C1] only when you rely on retrieved context. "
            "If compare mode is active, explicitly state the direction and size of the key deltas. "
            "If the user asks about substitution through 2024, explain the HS 8542 versus HS 3818 evidence clearly. "
            "For questions about a specific year or apparent drop, first determine whether that year is actually the dip "
            "or shock year relative to adjacent years; if not, say so plainly and point to the correct adjacent year. "
            "Use the provided year context notes when they are available. "
            "Do not hedge when the data clearly supports a conclusion. Distinguish historical evidence through 2024 from "
            "forecast or synthetic scenarios for 2025-2027."
        )

        facts_block = "\n".join(f"- {fact}" for fact in exact_facts) if exact_facts else "- No exact facts extracted."
        citation_block = (
            "\n".join(
                f"[{citation.label}] {citation.title} | {citation.source}\n{citation.snippet}"
                for citation in citations
            )
            if citations
            else "No retrieved context."
        )
        ui_context = [
            f"Active tab: {request.active_tab or 'unknown'}",
            f"Chart: {request.chart_id or 'none'}",
            f"Selected year: {request.selected_year or 'none'}",
            f"Compare year: {request.compare_year or 'none'}",
        ]

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Question:\n"
                    f"{request.question}\n\n"
                    "UI context:\n"
                    + "\n".join(ui_context)
                    + "\n\nExact facts:\n"
                    + facts_block
                    + "\n\nRetrieved context:\n"
                    + citation_block
                    + "\n\nInstructions:\n"
                    "- Lead with the answer, not with uncertainty.\n"
                    "- Prefer exact facts when they resolve the question.\n"
                    "- Mention concrete years and deltas when comparing periods.\n"
                    "- If the question names a year and asks why it moved, say whether that year is actually the drop or just adjacent to it.\n"
                    "- Keep the response concise and readable in the dashboard chat panel.\n"
                    "- Do not invent values, sources, or claims beyond the supplied context.\n"
                    "- Do not include a 'Sources' section because the UI already shows supporting citations.\n"
                ),
            },
        ]

        for turn in request.conversation[-6:]:
            messages.insert(-1, {"role": turn.role, "content": turn.content})

        response = self._client_or_create().chat.completions.create(
            model=self.settings.groq_model,
            temperature=0.1,
            max_completion_tokens=650,
            messages=messages,
        )
        content = response.choices[0].message.content or ""
        return self._clean_answer(content, request.question)

    def _fallback_answer(self, exact_facts: list[str], citations: list[Citation]) -> str:
        if exact_facts:
            fallback = " ".join(exact_facts[:3])
            if citations:
                labels = ", ".join(citation.label for citation in citations[:2])
                return f"{fallback} Supporting retrieved context is attached in {labels}."
            return fallback

        if citations:
            return (
                "GROQ_API_KEY is not set, so I could not generate a model answer. "
                "The supporting local context is attached below."
            )

        return "GROQ_API_KEY is not set, and no retrieval context was available for this question."

    def _clean_answer(self, answer: str, question: str) -> str:
        cleaned = answer.replace("\r\n", "\n").strip()
        if not cleaned:
            return ""

        if not self._wants_headings(question):
            cleaned = re.sub(r"^\s{0,3}#{1,6}\s*", "", cleaned, flags=re.MULTILINE)

        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"(?is)\n{2,}(sources|citations)\s*:\s*\n.*$", "", cleaned).strip()
        return cleaned

    @staticmethod
    def _wants_headings(question: str) -> bool:
        question_lower = question.lower()
        return any(token in question_lower for token in ("heading", "headings", "outline", "structured", "sections"))

    def _client_or_create(self) -> Groq:
        if self._client is None:
            self._client = Groq(api_key=self.settings.groq_api_key)
        return self._client

    @staticmethod
    def _extract_years(text: str) -> set[int]:
        return {int(match) for match in re.findall(r"\b(19\d{2}|20\d{2})\b", text or "")}

    @staticmethod
    def _trim(text: str, limit: int) -> str:
        text = " ".join(text.split())
        return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
