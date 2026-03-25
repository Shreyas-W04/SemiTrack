"""
run_pipeline.py - Print the notebook order for the SemiTrack analytics workflow.

Usage:
  python run_pipeline.py            # list all notebooks in order
  python run_pipeline.py --step 3  # show one specific notebook
"""

from pathlib import Path
import sys


STEPS = [
    (1, Path("notebooks/01_preprocessing_walkthrough.ipynb"), "Preprocessing & feature engineering"),
    (2, Path("notebooks/02_eda_walkthrough.ipynb"), "Exploratory data analysis"),
    (3, Path("notebooks/03_stationarity_walkthrough.ipynb"), "Stationarity & structural break tests"),
    (4, Path("notebooks/04_arima_walkthrough.ipynb"), "ARIMA baseline model"),
    (5, Path("notebooks/05_arimax_walkthrough.ipynb"), "ARIMAX with policy dummies"),
    (6, Path("notebooks/06_mixshift_walkthrough.ipynb"), "Mix shift analysis"),
    (7, Path("notebooks/07_policy_report_charts_walkthrough.ipynb"), "Minister-facing policy report charts"),
]


def parse_specific_step() -> int | None:
    if "--step" not in sys.argv:
        return None

    idx = sys.argv.index("--step")
    try:
        return int(sys.argv[idx + 1])
    except (IndexError, ValueError):
        print("Usage: python run_pipeline.py --step N")
        raise SystemExit(1)


def print_step(num: int, notebook: Path, description: str) -> None:
    status = "OK" if notebook.exists() else "MISSING"
    print(f"{num}. [{status}] {description}")
    print(f"   {notebook.as_posix()}")


def main() -> int:
    specific = parse_specific_step()
    steps = [step for step in STEPS if specific is None or step[0] == specific]
    if not steps:
        print(f"No notebook step {specific} found.")
        return 1

    print("\n" + "=" * 65)
    print("  SEMITRACK INDIA - Notebook Workflow")
    print("=" * 65)
    print("Open the notebooks below in order and run them top-to-bottom.\n")

    for num, notebook, description in steps:
        print_step(num, notebook, description)

    print("\nCharts:  outputs/charts/")
    print("Reports: outputs/reports/")
    print("Backend: uvicorn backend.app:app --reload")
    print("Frontend: cd frontend && npm run dev")
    print("=" * 65 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
