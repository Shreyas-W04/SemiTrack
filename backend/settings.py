from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_dir: Path = ROOT_DIR / "data"
    outputs_dir: Path = ROOT_DIR / "outputs"
    reports_dir: Path = outputs_dir / "reports"
    charts_dir: Path = outputs_dir / "charts"

    annual_file: Path = data_dir / "processed" / "india_semiconductor_integrated_annual.csv"
    country_file: Path = data_dir / "processed" / "india_semiconductor_country_year_breakdown.csv"
    synthetic_file: Path = data_dir / "synthetic" / "actual_imports_2025_2026.csv"
    forecast_file: Path = reports_dir / "arimax_forecast_values.csv"
    evaluation_file: Path = reports_dir / "arimax_evaluation.txt"
    policy_report_file: Path = reports_dir / "india_semiconductor_policy_report.md"
    model_eval_file: Path = reports_dir / "model_evaluation.csv"
    stationarity_report_file: Path = reports_dir / "stationarity_report.txt"
    mixshift_report_file: Path = reports_dir / "mixshift_report.txt"

    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    vector_store: str = os.getenv("VECTOR_STORE", "memory").strip().lower()
    chroma_dir: Path = Path(os.getenv("CHROMA_DIR", str(ROOT_DIR / ".cache" / "semichat-chroma")))
    cors_origins: tuple[str, ...] = _split_csv(
        os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
