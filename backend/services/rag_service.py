from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

from backend.rag.chart_catalog import CHART_CATALOG
from backend.settings import Settings


@dataclass
class SourceDocument:
    doc_id: str
    text: str
    metadata: dict[str, Any]
    score: float | None = None


class HashingEmbedder:
    def __init__(self, n_features: int = 2048) -> None:
        self.vectorizer = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm="l2",
            ngram_range=(1, 2),
        )

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return self.vectorizer.transform(texts).toarray().astype("float32")

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed_texts([text])[0]


class MemoryVectorStore:
    backend_name = "memory"

    def __init__(self, documents: list[SourceDocument], embedder: HashingEmbedder) -> None:
        self.documents = documents
        self.embedder = embedder
        self.matrix = self.embedder.embed_texts([document.text for document in documents])

    def search(self, query: str, top_k: int) -> list[SourceDocument]:
        query_vector = self.embedder.embed_query(query)
        scores = self.matrix @ query_vector
        indices = np.argsort(scores)[::-1][:top_k]
        results: list[SourceDocument] = []
        for index in indices:
            document = self.documents[int(index)]
            results.append(
                SourceDocument(
                    doc_id=document.doc_id,
                    text=document.text,
                    metadata=document.metadata,
                    score=float(scores[index]),
                )
            )
        return results


class ChromaVectorStore:
    backend_name = "chroma"

    def __init__(self, settings: Settings, documents: list[SourceDocument], embedder: HashingEmbedder) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("chromadb is not installed. Install it or switch VECTOR_STORE=memory.") from exc

        self.embedder = embedder
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        try:
            client.delete_collection("semichat")
        except Exception:
            pass

        self.collection = client.get_or_create_collection(name="semichat", metadata={"hnsw:space": "cosine"})
        self.collection.add(
            ids=[document.doc_id for document in documents],
            documents=[document.text for document in documents],
            embeddings=self.embedder.embed_texts([document.text for document in documents]).tolist(),
            metadatas=[self._sanitize_metadata(document.metadata) for document in documents],
        )

    @staticmethod
    def _sanitize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        sanitized: dict[str, Any] = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        return sanitized

    def search(self, query: str, top_k: int) -> list[SourceDocument]:
        result = self.collection.query(
            query_embeddings=[self.embedder.embed_query(query).tolist()],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            SourceDocument(
                doc_id=doc_id,
                text=text,
                metadata=metadata or {},
                score=None if distance is None else max(0.0, 1 - float(distance)),
            )
            for doc_id, text, metadata, distance in zip(ids, docs, metas, distances)
        ]


class RetrievalService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.documents = self._build_documents()
        self.embedder = HashingEmbedder()
        self.store = self._build_store()
        self.backend_name = self.store.backend_name

    def _build_store(self):
        if self.settings.vector_store == "chroma":
            try:
                return ChromaVectorStore(self.settings, self.documents, self.embedder)
            except RuntimeError:
                return MemoryVectorStore(self.documents, self.embedder)
        return MemoryVectorStore(self.documents, self.embedder)

    def search(self, query: str, top_k: int = 4) -> list[SourceDocument]:
        return self.store.search(query, top_k)

    def _build_documents(self) -> list[SourceDocument]:
        documents: list[SourceDocument] = []
        documents.extend(self._chunk_markdown_file(self.settings.policy_report_file, "report"))
        for path in [
            self.settings.evaluation_file,
            self.settings.stationarity_report_file,
            self.settings.mixshift_report_file,
        ]:
            documents.extend(self._chunk_text_file(path, "report"))

        for chart in CHART_CATALOG:
            text = (
                f"{chart['title']}\n"
                f"Tab: {chart['tab']}\n"
                f"Summary: {chart['summary']}\n"
                f"Source files: {', '.join(chart['source_files'])}"
            )
            documents.append(
                SourceDocument(
                    doc_id=f"chart-{chart['id']}",
                    text=text,
                    metadata={
                        "title": chart["title"],
                        "source": "chart_catalog",
                        "kind": "chart",
                        "chart_id": chart["id"],
                    },
                )
            )
        return documents

    def _chunk_markdown_file(self, path, source_kind: str) -> list[SourceDocument]:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        sections: list[tuple[str, str]] = []
        current_heading = "Document"
        buffer: list[str] = []
        for line in lines:
            if line.startswith("## ") or line.startswith("### "):
                if buffer:
                    sections.append((current_heading, "\n".join(buffer).strip()))
                    buffer = []
                current_heading = line.lstrip("# ").strip()
            else:
                buffer.append(line)
        if buffer:
            sections.append((current_heading, "\n".join(buffer).strip()))

        documents: list[SourceDocument] = []
        for index, (heading, content) in enumerate(sections, start=1):
            for chunk_index, chunk in enumerate(self._chunk_text(content), start=1):
                documents.append(
                    SourceDocument(
                        doc_id=f"{path.stem}-{index}-{chunk_index}",
                        text=f"{heading}\n{chunk}",
                        metadata={
                            "title": heading,
                            "source": str(path.relative_to(self.settings.root_dir)),
                            "kind": source_kind,
                        },
                    )
                )
        return documents

    def _chunk_text_file(self, path, source_kind: str) -> list[SourceDocument]:
        text = path.read_text(encoding="utf-8")
        return [
            SourceDocument(
                doc_id=f"{path.stem}-{index}",
                text=chunk,
                metadata={
                    "title": path.name,
                    "source": str(path.relative_to(self.settings.root_dir)),
                    "kind": source_kind,
                },
            )
            for index, chunk in enumerate(self._chunk_text(text), start=1)
        ]

    @staticmethod
    def _chunk_text(text: str, target_size: int = 900, overlap: int = 120) -> list[str]:
        cleaned = " ".join(text.split())
        if len(cleaned) <= target_size:
            return [cleaned]
        chunks: list[str] = []
        start = 0
        while start < len(cleaned):
            end = min(len(cleaned), start + target_size)
            chunk = cleaned[start:end]
            if end < len(cleaned):
                split = chunk.rfind(". ")
                if split > target_size // 2:
                    end = start + split + 1
                    chunk = cleaned[start:end]
            chunks.append(chunk.strip())
            if end >= len(cleaned):
                break
            start = max(end - overlap, start + 1)
        return chunks
