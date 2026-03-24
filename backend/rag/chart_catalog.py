CHART_CATALOG = [
    {
        "id": "trajectory",
        "tab": "overview",
        "title": "Total imports and ARIMAX baseline",
        "summary": (
            "Shows the long-run nominal and real import bill, then extends the series with the "
            "ARIMAX 2025-2027 baseline forecast and confidence interval."
        ),
        "source_files": [
            "data/processed/india_semiconductor_integrated_annual.csv",
            "outputs/reports/arimax_forecast_values.csv",
        ],
    },
    {
        "id": "acceleration",
        "tab": "overview",
        "title": "Post-2018 acceleration",
        "summary": (
            "Indexes real and nominal imports to 2017=100 so the 2018 regime change and the "
            "post-COVID rebound are easier to compare."
        ),
        "source_files": ["data/processed/india_semiconductor_integrated_annual.csv"],
    },
    {
        "id": "supplierBreakdown",
        "tab": "overview",
        "title": "2024 supplier breakdown",
        "summary": (
            "Ranks the 2024 supplier basket by market share, import value, and a geo-risk score "
            "used in the dashboard's risk framing."
        ),
        "source_files": ["data/processed/india_semiconductor_country_year_breakdown.csv"],
    },
    {
        "id": "shareTrends",
        "tab": "overview",
        "title": "China share versus non-China share",
        "summary": (
            "Tracks the rise of China as the dominant single supplier node across 1995-2024 and "
            "contrasts it with the rest of the basket."
        ),
        "source_files": ["data/processed/india_semiconductor_integrated_annual.csv"],
    },
    {
        "id": "riskCorrelation",
        "tab": "overview",
        "title": "China share and HHI risk zone",
        "summary": (
            "Plots China's market share against supplier concentration to show how dependence and "
            "concentration move together, especially after 2018."
        ),
        "source_files": ["data/processed/india_semiconductor_integrated_annual.csv"],
    },
    {
        "id": "productMix",
        "tab": "import",
        "title": "HS 8542 versus HS 3818 product mix",
        "summary": (
            "Compares finished integrated-circuit imports with semiconductor-material imports and "
            "shows how overwhelmingly the basket is dominated by HS 8542."
        ),
        "source_files": ["data/processed/india_semiconductor_integrated_annual.csv"],
    },
    {
        "id": "yearContext",
        "tab": "year",
        "title": "Year analysis historical context",
        "summary": (
            "Places a selected year inside the full nominal and real import timeline so the user can "
            "compare single-year snapshots against the long-run curve."
        ),
        "source_files": ["data/processed/india_semiconductor_integrated_annual.csv"],
    },
    {
        "id": "yoyGrowth",
        "tab": "import",
        "title": "Year-on-year real growth",
        "summary": (
            "Highlights the volatility of real import growth across the full series, including "
            "sharp slowdowns and the post-2020 rebound."
        ),
        "source_files": ["data/processed/india_semiconductor_integrated_annual.csv"],
    },
    {
        "id": "volatility",
        "tab": "import",
        "title": "Three-year rolling volatility",
        "summary": (
            "Measures the short-run instability of growth rates to show how the import bill has "
            "become both larger and more episodically volatile."
        ),
        "source_files": ["data/processed/india_semiconductor_integrated_annual.csv"],
    },
    {
        "id": "substitutionHs8542",
        "tab": "subst",
        "title": "HS 8542 substitution check",
        "summary": (
            "Tests whether finished-chip imports fall below the BAU forecast, which is required "
            "for a substitution signal."
        ),
        "source_files": [
            "data/processed/india_semiconductor_integrated_annual.csv",
            "data/synthetic/actual_imports_2025_2026.csv",
        ],
    },
    {
        "id": "substitutionHs3818",
        "tab": "subst",
        "title": "HS 3818 substitution check",
        "summary": (
            "Tests whether upstream semiconductor-material imports rise above the BAU forecast, "
            "which would complement an HS 8542 drop in a packaging-led substitution story."
        ),
        "source_files": [
            "data/processed/india_semiconductor_integrated_annual.csv",
            "data/synthetic/actual_imports_2025_2026.csv",
        ],
    },
    {
        "id": "riskCorridor",
        "tab": "risk",
        "title": "China share and HHI corridor",
        "summary": (
            "Compares China share and HHI on the same timeline to show that the post-2018 period "
            "is both larger and more concentrated."
        ),
        "source_files": ["data/processed/india_semiconductor_integrated_annual.csv"],
    },
    {
        "id": "riskScore",
        "tab": "risk",
        "title": "Composite supply-chain risk score",
        "summary": (
            "Builds a simple 0-10 composite risk indicator from China exposure and concentration "
            "so policymakers can track worsening fragility over time."
        ),
        "source_files": ["data/processed/india_semiconductor_integrated_annual.csv"],
    },
    {
        "id": "hhi",
        "tab": "risk",
        "title": "Supplier concentration index",
        "summary": (
            "Shows the Herfindahl-Hirschman Index and flags when the supplier base enters a high-"
            "concentration regime."
        ),
        "source_files": ["data/processed/india_semiconductor_integrated_annual.csv"],
    },
]
