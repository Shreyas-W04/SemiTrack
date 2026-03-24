from __future__ import annotations

import io
import re

import pandas as pd

from backend.rag.chart_catalog import CHART_CATALOG
from backend.schemas import SubstitutionPreviewResponse
from backend.settings import Settings


SHOCK_TIMELINE = [
    {
        "year": "2008",
        "text": "Global financial crisis cuts electronics demand and trade finance, producing a visible import dip.",
    },
    {
        "year": "2018+",
        "text": "Electronics-led growth pushes the series into a faster import regime that remains the new baseline.",
    },
    {
        "year": "2020",
        "text": "COVID disrupts logistics and industrial demand, but the setback is temporary rather than structural.",
    },
    {
        "year": "2021-22",
        "text": "Chip shortages and recovery demand lift dependence from an already higher base.",
    },
]

KEY_INSIGHTS = [
    {
        "kicker": "Scale",
        "title": "The import bill compounds upward.",
        "copy": "Nominal imports rise from roughly $0.24B in 1995 to $23.05B in 2024, with no structural decline yet visible.",
    },
    {
        "kicker": "Mix",
        "title": "HS 8542 still dominates the basket.",
        "copy": "Finished integrated circuits account for almost all tracked value, while upstream materials remain a small share.",
    },
    {
        "kicker": "Dependence",
        "title": "China exposure deepened materially.",
        "copy": "China moves from negligible share in the 1990s to the single largest supplier node by 2024.",
    },
    {
        "kicker": "Concentration",
        "title": "Supplier diversification is shallow.",
        "copy": "The HHI rises into a high-concentration zone even though more countries appear in the basket.",
    },
    {
        "kicker": "Verdict",
        "title": "No historical substitution through 2024.",
        "copy": "A real substitution story needs finished-chip imports to flatten or fall while materials rise. That divergence is absent historically.",
    },
]

YEAR_NOTES = {
    2008: "Global financial crisis compresses electronics demand and trade finance, creating a visible slowdown.",
    2018: "The dataset marks 2018 as the start of a faster electronics-led import regime.",
    2020: "Pandemic disruption creates a temporary break, but the broader dependence story resumes quickly.",
    2021: "Global chip shortages keep the system strained while dependence remains elevated.",
    2022: "The higher post-2018 regime persists even after the immediate shortage shock cools.",
    2023: "Materials imports move, but finished-chip imports still do not break the broader dependence pattern.",
    2024: "Imports set new highs and the historical record still does not show substitution.",
}

YEAR_REASON_TRIGGERS = (
    "why",
    "what happened",
    "sudden",
    "drop",
    "drops",
    "dip",
    "dips",
    "shock",
    "slowdown",
    "decline",
    "fall",
    "fell",
    "slump",
    "spike",
)

RISK_SCORE_OVERRIDES = {
    "China": 9.0,
    "Taiwan": 8.5,
    "South Korea": 4.5,
    "Japan": 3.0,
    "Malaysia": 4.0,
    "Singapore": 3.0,
    "Other": 5.0,
    "Israel": 5.0,
    "Hong Kong": 7.0,
    "Philippines": 3.0,
    "USA": 3.5,
    "Germany": 3.5,
}

TAB_META = [
    {"id": "overview", "label": "Overview"},
    {"id": "import", "label": "Import Analysis"},
    {"id": "year", "label": "Year Analysis"},
    {"id": "subst", "label": "Substitution Tracker"},
    {"id": "risk", "label": "Supplier Risk"},
]

COMPARE_ANCHOR_YEAR = 2018


def _round_or_none(value: float | int | None, digits: int = 2) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)


def _first_matching_column(columns: list[str], patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        for column in columns:
            if pattern in column:
                return column
    return None


def _extract_years_from_text(text: str) -> set[int]:
    return {int(match) for match in re.findall(r"\b(19\d{2}|20\d{2})\b", text or "")}


class DashboardService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.annual = self._load_annual()
        self.country = self._load_country()
        self.forecast = self._load_forecast()
        self.synthetic = self._load_synthetic()
        self.chart_catalog = {item["id"]: item for item in CHART_CATALOG}
        self._dashboard_payload: dict | None = None

    def _load_annual(self) -> pd.DataFrame:
        annual = pd.read_csv(self.settings.annual_file)
        numeric_cols = [
            "year",
            "import_value_usd_billions",
            "real_value_2015usd_billions",
            "total_import_value_usd",
            "real_import_value_2015usd",
            "hs8542_import_usd",
            "hs8542_share_pct",
            "hs3818_import_usd",
            "hs3818_share_pct",
            "yoy_nominal_growth_pct",
            "yoy_real_growth_pct",
            "num_exporting_countries",
            "top3_supplier_share_pct",
            "china_import_usd",
            "china_share_pct",
            "supplier_hhi",
        ]
        for column in numeric_cols:
            if column in annual.columns:
                annual[column] = pd.to_numeric(annual[column], errors="coerce")

        annual["year"] = annual["year"].astype(int)
        annual["hs8542_import_bn"] = annual["hs8542_import_usd"] / 1_000_000_000
        annual["hs3818_import_bn"] = annual["hs3818_import_usd"] / 1_000_000_000
        annual["non_china_share_pct"] = 100 - annual["china_share_pct"]
        annual["hhi_x100"] = annual["supplier_hhi"] * 100

        base_2017 = annual.loc[annual["year"] == 2017].iloc[0]
        annual["real_index_2017"] = annual["real_value_2015usd_billions"] / base_2017["real_value_2015usd_billions"] * 100
        annual["nominal_index_2017"] = annual["import_value_usd_billions"] / base_2017["import_value_usd_billions"] * 100

        yoy = annual["yoy_real_growth_pct"].tolist()
        rolling_volatility: list[float | None] = []
        for index, _ in enumerate(yoy):
            if index < 2:
                rolling_volatility.append(None)
                continue
            window = [value for value in yoy[max(1, index - 2) : index + 1] if pd.notna(value)]
            if not window:
                rolling_volatility.append(None)
                continue
            mean = sum(window) / len(window)
            variance = sum((value - mean) ** 2 for value in window) / len(window)
            rolling_volatility.append(variance**0.5)
        annual["rolling_volatility"] = rolling_volatility
        return annual

    def _load_country(self) -> pd.DataFrame:
        country = pd.read_csv(self.settings.country_file)
        numeric_cols = [
            "year",
            "import_value_usd",
            "quantity_mt",
            "num_products",
            "year_total_usd",
            "market_share_pct",
        ]
        for column in numeric_cols:
            if column in country.columns:
                country[column] = pd.to_numeric(country[column], errors="coerce")
        country["year"] = country["year"].astype(int)
        country["import_value_bn"] = country["import_value_usd"] / 1_000_000_000
        country["risk_score"] = country["exporter_name"].map(RISK_SCORE_OVERRIDES).fillna(5.0)
        country["risk_level"] = country["risk_score"].apply(self._risk_level)
        return country

    def _load_forecast(self) -> pd.DataFrame:
        forecast = pd.read_csv(self.settings.forecast_file)
        for column in ["year", "arimax_forecast_bn", "ci_lower_bn", "ci_upper_bn", "aic"]:
            if column in forecast.columns:
                forecast[column] = pd.to_numeric(forecast[column], errors="coerce")
        forecast["year"] = forecast["year"].astype(int)
        return forecast

    def _load_synthetic(self) -> pd.DataFrame:
        synthetic = pd.read_csv(self.settings.synthetic_file)
        numeric_cols = [
            "year",
            "hs_code",
            "bau_forecast_real_2015usd_bn",
            "actual_value_real_2015usd_bn",
            "delta_bn",
        ]
        for column in numeric_cols:
            if column in synthetic.columns:
                synthetic[column] = pd.to_numeric(synthetic[column], errors="coerce")
        synthetic["year"] = synthetic["year"].astype(int)
        synthetic["hs_code"] = synthetic["hs_code"].astype(str).str.strip()
        synthetic["period"] = synthetic["period"].astype(str).str.strip().str.lower()
        return synthetic

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 8:
            return "Critical"
        if score >= 6:
            return "High"
        if score >= 4:
            return "Moderate"
        return "Low"

    def get_dashboard_payload(self) -> dict:
        if self._dashboard_payload is None:
            self._dashboard_payload = self._build_dashboard_payload()
        return self._dashboard_payload

    def _build_dashboard_payload(self) -> dict:
        annual = self.annual.copy()
        latest = annual.iloc[-1]
        countries_2024 = self.country[self.country["year"] == 2024].sort_values("market_share_pct", ascending=False).head(10)
        weighted_risk = float((countries_2024["market_share_pct"] / 100 * countries_2024["risk_score"]).sum())
        risk_slice = annual[annual["year"] >= 2010].copy()
        risk_slice["risk_score"] = (risk_slice["china_share_pct"] / 100 * 9 + risk_slice["supplier_hhi"] * 15).clip(upper=9.5)

        overview_trajectory = [
            {
                "year": int(row.year),
                "nominal": _round_or_none(row.import_value_usd_billions, 2),
                "real": _round_or_none(row.real_value_2015usd_billions, 2),
                "forecast": None,
                "forecastLower": None,
                "forecastUpper": None,
            }
            for row in annual.itertuples()
        ]
        overview_trajectory.extend(
            [
                {
                    "year": int(row.year),
                    "nominal": None,
                    "real": None,
                    "forecast": _round_or_none(row.arimax_forecast_bn, 2),
                    "forecastLower": _round_or_none(row.ci_lower_bn, 2),
                    "forecastUpper": _round_or_none(row.ci_upper_bn, 2),
                }
                for row in self.forecast.itertuples()
            ]
        )

        year_details = {
            str(int(row.year)): {
                "year": int(row.year),
                "nominalBill": _round_or_none(row.import_value_usd_billions, 2),
                "realBill": _round_or_none(row.real_value_2015usd_billions, 2),
                "chinaShare": _round_or_none(row.china_share_pct, 2),
                "nonChinaShare": _round_or_none(row.non_china_share_pct, 2),
                "hhi": _round_or_none(row.supplier_hhi, 3),
                "hhiX100": _round_or_none(row.hhi_x100, 1),
                "hs8542Bill": _round_or_none(row.hs8542_import_bn, 3),
                "hs3818Bill": _round_or_none(row.hs3818_import_bn, 3),
                "hs8542Share": _round_or_none(row.hs8542_share_pct, 2),
                "hs3818Share": _round_or_none(row.hs3818_share_pct, 2),
                "topExporter": row.top_exporter_name,
                "top3Share": _round_or_none(row.top3_supplier_share_pct, 2),
                "yoyReal": _round_or_none(row.yoy_real_growth_pct, 2),
                "yoyNominal": _round_or_none(row.yoy_nominal_growth_pct, 2),
                "numExporters": int(row.num_exporting_countries),
                "eventNote": YEAR_NOTES.get(
                    int(row.year),
                    "No explicit note stored for this year; use the trend and supplier metrics for interpretation.",
                ),
            }
            for row in annual.itertuples()
        }

        substitution_defaults = self._build_substitution_series()
        default_preview = self._compute_substitution_preview_from_rows(self.synthetic)

        return {
            "meta": {
                "title": "SemiTrack India",
                "subtitle": "Semiconductor Import Substitution Tracker",
                "chips": [
                    "HS 8542 + HS 3818",
                    "CEPII BACI HS92 V202601",
                    "1995-2024 historical + ARIMAX 2025-2027",
                ],
                "footer": {
                    "left": "SemiTrack India | CEPII BACI HS92 V202601 | World Bank WDI deflators",
                    "right": "Groq chat + local retrieval over reports, chart notes, and processed data",
                },
            },
            "tabs": TAB_META,
            "overview": {
                "hero": {
                    "eyebrow": "Executive command center",
                    "title": "India's semiconductor import bill is scaling faster than any visible substitution signal.",
                    "description": (
                        "The 1995-2024 trade record points to a sharper post-2018 import regime, overwhelming HS 8542 "
                        "dominance, and deeper dependence on a narrow East Asian supplier base. This React surface mirrors "
                        "the existing dashboard while adding retrieval-aware chat over the underlying data and reports."
                    ),
                    "pills": [
                        "React dashboard shell",
                        "Historical + forecast framing",
                        "RAG chat over data and chart notes",
                    ],
                    "stats": [
                        {
                            "label": "2024 import bill",
                            "value": f"${latest.import_value_usd_billions:.2f}B",
                            "copy": "Nominal imports are nearly 100x the 1995 level and continue rising after the 2020 disruption.",
                        },
                        {
                            "label": "Structural break",
                            "value": "2018",
                            "copy": "The report flags 2018 as the transition into a faster electronics-led import growth regime.",
                        },
                        {
                            "label": "China share",
                            "value": f"{latest.china_share_pct:.1f}%",
                            "copy": "China remains the single largest supplier node in 2024 even after the 2023 spike cools slightly.",
                        },
                        {
                            "label": "Historical verdict",
                            "value": "No",
                            "copy": "There is still no substitution evidence because finished-chip imports continue to set new highs.",
                        },
                    ],
                    "timeline": SHOCK_TIMELINE,
                },
                "insights": KEY_INSIGHTS,
                "charts": {
                    "trajectory": {
                        "id": "trajectory",
                        "title": "Total imports and ARIMAX baseline",
                        "subtitle": "Nominal and real series through 2024, with BAU forecast through 2027",
                        "insight": (
                            "Imports trend upward across the full sample, with visible setbacks around 2008 and 2020. "
                            "The slope steepens after 2018, consistent with deeper downstream dependence."
                        ),
                        "data": overview_trajectory,
                    },
                    "acceleration": {
                        "id": "acceleration",
                        "title": "Post-2018 acceleration from a 2017 base",
                        "subtitle": "Indexed to 2017=100 to make the regime shift easier to compare",
                        "insight": (
                            "Using 2017 as a common base makes the post-2018 re-rating clear: the 2020 dip is temporary, "
                            "while the 2021-2024 level remains materially higher."
                        ),
                        "data": [
                            {
                                "year": int(row.year),
                                "realIndex": _round_or_none(row.real_index_2017, 1),
                                "nominalIndex": _round_or_none(row.nominal_index_2017, 1),
                            }
                            for row in annual.itertuples()
                        ],
                    },
                    "supplierBreakdown": {
                        "id": "supplierBreakdown",
                        "title": "2024 supplier breakdown",
                        "subtitle": "Top supplier nodes by market share, value, and geo-risk",
                        "insight": (
                            "China, Taiwan, and South Korea dominate the current sourcing stack. The basket may look broader, "
                            "but value concentration remains severe."
                        ),
                        "data": self._country_rows(countries_2024),
                    },
                    "shareTrends": {
                        "id": "shareTrends",
                        "title": "China versus non-China share",
                        "subtitle": "Long-run market share shift across the import basket",
                        "insight": (
                            "China's share rises from below 1% in 1995 to nearly 46% in 2024. The broader concentration story "
                            "persists even after the 2024 easing from the 2023 spike."
                        ),
                        "data": [
                            {
                                "year": int(row.year),
                                "chinaShare": _round_or_none(row.china_share_pct, 2),
                                "nonChinaShare": _round_or_none(row.non_china_share_pct, 2),
                            }
                            for row in annual.itertuples()
                        ],
                    },
                    "riskCorrelation": {
                        "id": "riskCorrelation",
                        "title": "China share and HHI risk zone",
                        "subtitle": "Post-2018 points cluster in a higher dependence and concentration zone",
                        "insight": (
                            "After 2018, a larger China share arrives alongside a more concentrated supplier base. "
                            "That means dependence and geopolitical concentration are now reinforcing each other."
                        ),
                        "data": [
                            {
                                "year": int(row.year),
                                "period": "1995-2017" if int(row.year) < 2018 else "2018-2024",
                                "chinaShare": _round_or_none(row.china_share_pct, 2),
                                "hhiX100": _round_or_none(row.hhi_x100, 1),
                                "nominalBill": _round_or_none(row.import_value_usd_billions, 2),
                            }
                            for row in annual.itertuples()
                        ],
                    },
                },
            },
            "importAnalysis": {
                "kpis": [
                    {
                        "label": "2024 real imports",
                        "value": f"${latest.real_value_2015usd_billions:.2f}B",
                        "delta": "Deflated to 2015 USD",
                        "tone": "green",
                    },
                    {
                        "label": "HS 8542 share",
                        "value": f"{latest.hs8542_share_pct:.2f}%",
                        "delta": "Finished chips dominate the basket",
                        "tone": "blue",
                    },
                    {
                        "label": "HS 3818 share",
                        "value": f"{latest.hs3818_share_pct:.2f}%",
                        "delta": "Upstream materials remain a very small slice",
                        "tone": "amber",
                    },
                    {
                        "label": "2024 real YoY",
                        "value": f"{latest.yoy_real_growth_pct:.1f}%",
                        "delta": "Growth still positive in the latest year",
                        "tone": "muted",
                    },
                ],
                "charts": {
                    "productMix": {
                        "id": "productMix",
                        "title": "HS 8542 versus HS 3818 product mix",
                        "subtitle": "Import value composition and HS 8542 share over time",
                        "insight": (
                            "The basket is overwhelmingly dominated by HS 8542 throughout the series. "
                            "That is why the historical record still looks like downstream dependence, not substitution."
                        ),
                        "data": [
                            {
                                "year": int(row.year),
                                "hs8542Bill": _round_or_none(row.hs8542_import_bn, 3),
                                "hs3818Bill": _round_or_none(row.hs3818_import_bn, 3),
                                "hs8542Share": _round_or_none(row.hs8542_share_pct, 2),
                            }
                            for row in annual.itertuples()
                        ],
                    },
                    "yoyGrowth": {
                        "id": "yoyGrowth",
                        "title": "Year-on-year real growth",
                        "subtitle": "Growth swings highlight both shocks and the new higher base",
                        "insight": (
                            "Growth is volatile, but the larger story is the higher level of dependence after 2018. "
                            "Temporary slowdowns do not translate into sustained import compression."
                        ),
                        "data": [
                            {
                                "year": int(row.year),
                                "yoyReal": _round_or_none(row.yoy_real_growth_pct, 2),
                            }
                            for row in annual.itertuples()
                            if pd.notna(row.yoy_real_growth_pct)
                        ],
                    },
                    "volatility": {
                        "id": "volatility",
                        "title": "Three-year rolling volatility",
                        "subtitle": "Short-run instability in the real import growth path",
                        "insight": "The import bill is not only larger now; it is also more exposed to episodic shocks and rebounds.",
                        "data": [
                            {
                                "year": int(row.year),
                                "volatility": _round_or_none(row.rolling_volatility, 2),
                            }
                            for row in annual.itertuples()
                        ],
                    },
                },
            },
            "yearAnalysis": {
                "defaultYear": 2024,
                "defaultCompareYear": COMPARE_ANCHOR_YEAR,
                "availableYears": annual["year"].astype(int).tolist(),
                "contextChart": {
                    "title": "Historical context",
                    "subtitle": "Nominal and real imports across the full timeline",
                    "data": [
                        {
                            "year": int(row.year),
                            "nominal": _round_or_none(row.import_value_usd_billions, 2),
                            "real": _round_or_none(row.real_value_2015usd_billions, 2),
                        }
                        for row in annual.itertuples()
                    ],
                },
                "yearDetails": year_details,
            },
            "substitutionTracker": {
                "uploadTitle": "Upload actual 2025 data",
                "uploadDescription": (
                    "Drop a CSV with year, hs code, and actual values to test the substitution logic against the BAU baseline. "
                    "If you do nothing, the page starts with the synthetic Micron-style demonstration file."
                ),
                "uploadFormat": "Expected columns: year, hs_code, and one actual-value column such as actual_value_real_2015usd_bn",
                "preview": default_preview.model_dump(),
                "charts": substitution_defaults,
            },
            "supplierRisk": {
                "kpis": [
                    {
                        "label": "Composite geo-risk",
                        "value": f"{weighted_risk:.2f}/10",
                        "delta": "Weighted by 2024 supplier share",
                        "tone": "red",
                    },
                    {
                        "label": "Supplier HHI 2024",
                        "value": f"{latest.supplier_hhi:.3f}",
                        "delta": "Above the 0.25 high-concentration threshold",
                        "tone": "amber",
                    },
                    {
                        "label": "China + Taiwan",
                        "value": f"{countries_2024[countries_2024['exporter_name'].isin(['China', 'Taiwan'])]['market_share_pct'].sum():.1f}%",
                        "delta": "Combined critical corridor exposure",
                        "tone": "red",
                    },
                    {
                        "label": "Low-risk suppliers",
                        "value": f"{countries_2024[countries_2024['risk_level'] == 'Low']['market_share_pct'].sum():.1f}%",
                        "delta": "Share coming from the dashboard's lower-risk bucket",
                        "tone": "green",
                    },
                ],
                "charts": {
                    "riskCorridor": {
                        "id": "riskCorridor",
                        "title": "China share and HHI corridor",
                        "subtitle": "Long-run risk corridor across 1995-2024",
                        "insight": (
                            "China share and HHI rise together after 2018, meaning the import system is both larger and more concentrated."
                        ),
                        "data": [
                            {
                                "year": int(row.year),
                                "chinaShare": _round_or_none(row.china_share_pct, 2),
                                "hhiX100": _round_or_none(row.hhi_x100, 1),
                            }
                            for row in annual.itertuples()
                        ],
                    },
                    "riskScore": {
                        "id": "riskScore",
                        "title": "Composite supply-chain risk score",
                        "subtitle": "Simple 0-10 indicator derived from China share and HHI",
                        "insight": (
                            "Risk trends upward as China exposure and concentration rise together. The high-risk pattern persists through 2024."
                        ),
                        "data": [
                            {
                                "year": int(row.year),
                                "riskScore": _round_or_none(row.risk_score, 2),
                            }
                            for row in risk_slice.itertuples()
                        ],
                    },
                    "hhi": {
                        "id": "hhi",
                        "title": "Supplier concentration index",
                        "subtitle": "HHI above 0.25 indicates a highly concentrated supplier base",
                        "insight": (
                            "The supplier base becomes structurally concentrated after 2018. Diversification should be judged by value dispersion, not supplier count."
                        ),
                        "data": [
                            {
                                "year": int(row.year),
                                "hhi": _round_or_none(row.supplier_hhi, 3),
                            }
                            for row in risk_slice.itertuples()
                        ],
                    },
                },
                "table": self._country_rows(countries_2024),
            },
            "chat": {
                "suggestions": [
                    "Why does the report say there is no substitution through 2024?",
                    "What changed after 2018?",
                    "Compare 2018 and 2024.",
                    "Which countries dominate the 2024 supplier basket?",
                    "Explain the HS 8542 versus HS 3818 logic.",
                ],
                "chartCatalog": CHART_CATALOG,
            },
        }

    def _country_rows(self, country_frame: pd.DataFrame) -> list[dict]:
        return [
            {
                "country": row.exporter_name,
                "share": _round_or_none(row.market_share_pct, 2),
                "value": _round_or_none(row.import_value_bn, 2),
                "risk": _round_or_none(row.risk_score, 1),
                "level": row.risk_level,
            }
            for row in country_frame.itertuples()
        ]

    def _build_substitution_series(self) -> dict:
        recent = self.annual.tail(8).copy()
        actuals = self.synthetic[
            (self.synthetic["year"] == 2025)
            & (self.synthetic["period"] == "full_year")
            & (self.synthetic["hs_code"].isin(["8542", "3818"]))
        ]
        row_8542 = actuals[actuals["hs_code"] == "8542"].iloc[0]
        row_3818 = actuals[actuals["hs_code"] == "3818"].iloc[0]

        hs8542_data = [
            {
                "year": int(row.year),
                "historical": _round_or_none(row.hs8542_import_bn, 3),
                "bau": None,
                "actual": None,
            }
            for row in recent.itertuples()
        ]
        hs8542_data.append(
            {
                "year": 2025,
                "historical": None,
                "bau": _round_or_none(row_8542["bau_forecast_real_2015usd_bn"], 3),
                "actual": _round_or_none(row_8542["actual_value_real_2015usd_bn"], 3),
            }
        )

        hs3818_data = [
            {
                "year": int(row.year),
                "historical": _round_or_none(row.hs3818_import_bn, 3),
                "bau": None,
                "actual": None,
            }
            for row in recent.itertuples()
        ]
        hs3818_data.append(
            {
                "year": 2025,
                "historical": None,
                "bau": _round_or_none(row_3818["bau_forecast_real_2015usd_bn"], 3),
                "actual": _round_or_none(row_3818["actual_value_real_2015usd_bn"], 3),
            }
        )

        return {
            "hs8542": {
                "id": "substitutionHs8542",
                "title": "HS 8542 substitution check",
                "subtitle": "Finished-chip imports must fall below BAU for substitution to register",
                "data": hs8542_data,
            },
            "hs3818": {
                "id": "substitutionHs3818",
                "title": "HS 3818 substitution check",
                "subtitle": "Materials imports must rise above BAU if domestic activity is absorbing upstream inputs",
                "data": hs3818_data,
            },
        }

    def get_year_snapshot(self, year: int) -> dict | None:
        return self.get_dashboard_payload()["yearAnalysis"]["yearDetails"].get(str(year))

    def get_chart_context(self, chart_id: str | None) -> dict | None:
        if not chart_id:
            return None
        return self.chart_catalog.get(chart_id)

    def compare_years(self, from_year: int, to_year: int) -> dict | None:
        if from_year == to_year:
            return None

        left = self.get_year_snapshot(from_year)
        right = self.get_year_snapshot(to_year)
        if not left or not right:
            return None

        def diff(key: str, digits: int) -> float | None:
            left_value = left.get(key)
            right_value = right.get(key)
            if left_value is None or right_value is None:
                return None
            return round(float(right_value) - float(left_value), digits)

        def ratio(key: str, digits: int = 2) -> float | None:
            left_value = left.get(key)
            right_value = right.get(key)
            if left_value in (None, 0) or right_value is None:
                return None
            return round(float(right_value) / float(left_value), digits)

        return {
            "fromYear": from_year,
            "toYear": to_year,
            "nominalDelta": diff("nominalBill", 2),
            "nominalRatio": ratio("nominalBill"),
            "realDelta": diff("realBill", 2),
            "realRatio": ratio("realBill"),
            "chinaShareDelta": diff("chinaShare", 2),
            "hhiDelta": diff("hhi", 3),
            "hs8542ShareDelta": diff("hs8542Share", 2),
            "hs3818ShareDelta": diff("hs3818Share", 2),
            "topExporterFrom": left.get("topExporter"),
            "topExporterTo": right.get("topExporter"),
            "topExporterChanged": left.get("topExporter") != right.get("topExporter"),
        }

    def _format_year_snapshot_fact(self, snapshot: dict) -> str:
        return (
            f"{snapshot['year']} snapshot: nominal imports ${snapshot['nominalBill']:.2f}B, "
            f"real imports ${snapshot['realBill']:.2f}B, China share {snapshot['chinaShare']:.2f}%, "
            f"supplier HHI {snapshot['hhi']:.3f}, HS 8542 share {snapshot['hs8542Share']:.2f}%, "
            f"HS 3818 share {snapshot['hs3818Share']:.2f}%, top exporter {snapshot['topExporter']}."
        )

    @staticmethod
    def _format_year_note_fact(snapshot: dict) -> str | None:
        note = snapshot.get("eventNote")
        if not note or note.startswith("No explicit note stored"):
            return None
        return f"{snapshot['year']} context: {note}"

    def _format_year_movement_fact(self, year: int) -> str | None:
        current = self.get_year_snapshot(year)
        previous = self.get_year_snapshot(year - 1)
        following = self.get_year_snapshot(year + 1)
        if not current:
            return None

        current_value = current.get("nominalBill")
        previous_value = previous.get("nominalBill") if previous else None
        next_value = following.get("nominalBill") if following else None
        if current_value is None:
            return None

        if previous_value is not None and next_value is not None:
            if current_value < previous_value:
                rebound_clause = (
                    f"then recovers to ${next_value:.2f}B in {year + 1}"
                    if next_value > current_value
                    else f"then moves to ${next_value:.2f}B in {year + 1}"
                )
                return (
                    f"{year} is an actual dip year: nominal imports fall from ${previous_value:.2f}B in {year - 1} "
                    f"to ${current_value:.2f}B in {year}, {rebound_clause}."
                )
            if current_value > previous_value and next_value < current_value:
                return (
                    f"{year} is not itself the drop year: nominal imports rise from ${previous_value:.2f}B in {year - 1} "
                    f"to ${current_value:.2f}B in {year}, then ease to ${next_value:.2f}B in {year + 1}."
                )
            if current_value > previous_value and next_value > current_value:
                return (
                    f"{year} is not a drop year: nominal imports keep rising from ${previous_value:.2f}B in {year - 1} "
                    f"to ${current_value:.2f}B in {year} and ${next_value:.2f}B in {year + 1}."
                )
            return (
                f"{year} sits between ${previous_value:.2f}B in {year - 1}, ${current_value:.2f}B in {year}, "
                f"and ${next_value:.2f}B in {year + 1}."
            )

        if previous_value is not None:
            direction = "rises" if current_value > previous_value else "falls" if current_value < previous_value else "holds flat"
            return f"From {year - 1} to {year}, nominal imports {direction} from ${previous_value:.2f}B to ${current_value:.2f}B."

        return None

    def _related_context_year(self, year: int) -> int | None:
        current = self.get_year_snapshot(year)
        previous = self.get_year_snapshot(year - 1)
        following = self.get_year_snapshot(year + 1)
        if not current or not previous or not following:
            return None

        current_value = current.get("nominalBill")
        previous_value = previous.get("nominalBill")
        next_value = following.get("nominalBill")
        if current_value is None or previous_value is None or next_value is None:
            return None

        if current_value > previous_value and next_value < current_value:
            return year + 1
        if current_value < previous_value and previous_value > current_value:
            return year
        return None

    def _format_year_comparison_fact(self, comparison: dict) -> str:
        def signed_billions(value: float | None) -> str:
            if value is None:
                return "n/a"
            sign = "+" if value >= 0 else "-"
            return f"{sign}${abs(value):.2f}B"

        def signed_points(value: float | None) -> str:
            return "n/a" if value is None else f"{value:+.2f} pp"

        def signed_number(value: float | None, digits: int = 3) -> str:
            return "n/a" if value is None else f"{value:+.{digits}f}"

        nominal_ratio = f" ({comparison['nominalRatio']:.2f}x)" if comparison["nominalRatio"] is not None else ""
        real_ratio = f" ({comparison['realRatio']:.2f}x)" if comparison["realRatio"] is not None else ""
        if comparison["topExporterChanged"]:
            exporter_note = (
                f"top exporter changed from {comparison['topExporterFrom']} to {comparison['topExporterTo']}"
            )
        else:
            exporter_note = f"top exporter unchanged at {comparison['topExporterTo']}"

        return (
            f"{comparison['fromYear']} -> {comparison['toYear']} comparison: nominal imports "
            f"{signed_billions(comparison['nominalDelta'])}{nominal_ratio}, real imports "
            f"{signed_billions(comparison['realDelta'])}{real_ratio}, China share "
            f"{signed_points(comparison['chinaShareDelta'])}, supplier HHI "
            f"{signed_number(comparison['hhiDelta'])}, HS 8542 share "
            f"{signed_points(comparison['hs8542ShareDelta'])}, HS 3818 share "
            f"{signed_points(comparison['hs3818ShareDelta'])}, {exporter_note}."
        )

    def _build_substitution_facts(self, latest_historical_year: int) -> list[str]:
        baseline_year = COMPARE_ANCHOR_YEAR if self.get_year_snapshot(COMPARE_ANCHOR_YEAR) else latest_historical_year
        baseline = self.get_year_snapshot(baseline_year)
        latest = self.get_year_snapshot(latest_historical_year)
        if not baseline or not latest:
            return []

        return [
            (
                f"Historical substitution check through {latest_historical_year}: HS 8542 imports rise from "
                f"${baseline['hs8542Bill']:.3f}B in {baseline_year} to ${latest['hs8542Bill']:.3f}B in "
                f"{latest_historical_year}, while HS 3818 is only ${latest['hs3818Bill']:.3f}B and "
                f"{latest['hs3818Share']:.2f}% share in {latest_historical_year}."
            ),
            (
                f"That is why the dashboard says there is no substitution through {latest_historical_year}: "
                "finished-chip imports do not flatten or fall, and upstream materials do not gain enough share to "
                "offset the dependence story."
            ),
        ]

    @staticmethod
    def _dedupe_facts(facts: list[str], limit: int = 10) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for fact in facts:
            cleaned = " ".join(fact.split())
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            unique.append(cleaned)
            if len(unique) >= limit:
                break
        return unique

    def build_exact_facts(
        self,
        question: str,
        selected_year: int | None = None,
        compare_year: int | None = None,
    ) -> list[str]:
        facts: list[str] = []
        question_lower = question.lower()
        mentioned_years = _extract_years_from_text(question)
        years = set(mentioned_years)
        if not mentioned_years:
            if selected_year:
                years.add(selected_year)
            if compare_year and compare_year != selected_year:
                years.add(compare_year)

        compare_triggers = (
            "compare",
            "comparison",
            "versus",
            " vs ",
            "difference",
            "different between",
            "changed from",
            "between",
        )
        if mentioned_years and any(trigger in question_lower for trigger in compare_triggers):
            if selected_year and (selected_year in mentioned_years or compare_year in mentioned_years):
                years.add(selected_year)
            if compare_year and (selected_year in mentioned_years or compare_year in mentioned_years):
                years.add(compare_year)

        wants_year_context = bool(mentioned_years) and any(trigger in question_lower for trigger in YEAR_REASON_TRIGGERS)

        latest_historical_year = int(self.annual["year"].max())
        compare_pairs: list[tuple[int, int]] = []
        if selected_year and compare_year and selected_year != compare_year and not mentioned_years:
            compare_pairs.append(tuple(sorted((selected_year, compare_year))))
        if len(years) >= 2 and any(trigger in question_lower for trigger in compare_triggers):
            compare_pairs.append((min(years), max(years)))

        for year in sorted(years):
            snapshot = self.get_year_snapshot(year)
            if snapshot:
                facts.append(self._format_year_snapshot_fact(snapshot))
                if wants_year_context and year in mentioned_years:
                    note_fact = self._format_year_note_fact(snapshot)
                    if note_fact:
                        facts.append(note_fact)
                    movement_fact = self._format_year_movement_fact(year)
                    if movement_fact:
                        facts.append(movement_fact)
                    related_year = self._related_context_year(year)
                    if related_year and related_year not in mentioned_years:
                        related_snapshot = self.get_year_snapshot(related_year)
                        if related_snapshot:
                            related_note = self._format_year_note_fact(related_snapshot)
                            if related_note:
                                facts.append(related_note)
                continue

            forecast_row = self.forecast[self.forecast["year"] == year]
            if not forecast_row.empty:
                row = forecast_row.iloc[0]
                facts.append(
                    f"{year} BAU forecast: ${row['arimax_forecast_bn']:.3f}B real 2015 USD, "
                    f"with confidence interval ${row['ci_lower_bn']:.3f}B to ${row['ci_upper_bn']:.3f}B."
                )

            synthetic_rows = self.synthetic[(self.synthetic["year"] == year) & (self.synthetic["period"] == "full_year")]
            for row in synthetic_rows.itertuples():
                direction = "below" if row.actual_value_real_2015usd_bn < row.bau_forecast_real_2015usd_bn else "above"
                facts.append(
                    f"{year} synthetic {row.hs_code}: actual ${row.actual_value_real_2015usd_bn:.3f}B versus BAU "
                    f"${row.bau_forecast_real_2015usd_bn:.3f}B, so the signal is {direction} forecast."
                )

        post_2018_triggers = ("after 2018", "since 2018", "post-2018", "what changed after 2018", "changed after 2018")
        if any(phrase in question_lower for phrase in post_2018_triggers):
            compare_pairs.append((COMPARE_ANCHOR_YEAR, latest_historical_year))
            years.update({COMPARE_ANCHOR_YEAR, latest_historical_year})
            row_2020 = self.get_year_snapshot(2020)
            row_2018 = self.get_year_snapshot(COMPARE_ANCHOR_YEAR)
            row_latest = self.get_year_snapshot(latest_historical_year)
            if row_2018:
                facts.append(self._format_year_snapshot_fact(row_2018))
            if row_latest:
                facts.append(self._format_year_snapshot_fact(row_latest))
            if row_2020 and row_2018 and row_latest:
                facts.append(
                    f"2020 is a temporary dip inside the higher post-2018 regime: real imports move from "
                    f"${row_2018['realBill']:.2f}B in {COMPARE_ANCHOR_YEAR} to ${row_2020['realBill']:.2f}B in 2020, "
                    f"then recover to ${row_latest['realBill']:.2f}B by {latest_historical_year}."
                )

        unique_pairs: list[tuple[int, int]] = []
        for left, right in compare_pairs:
            pair = tuple(sorted((left, right)))
            if pair[0] == pair[1] or pair in unique_pairs:
                continue
            unique_pairs.append(pair)

        for left, right in unique_pairs:
            comparison = self.compare_years(left, right)
            if comparison:
                facts.append(self._format_year_comparison_fact(comparison))

        substitution_triggers = ("substitution", "hs 8542", "hs8542", "hs 3818", "hs3818")
        if any(trigger in question_lower for trigger in substitution_triggers):
            facts.extend(self._build_substitution_facts(latest_historical_year))

        latest_year = max(
            [year for year in years if self.get_year_snapshot(year)],
            default=latest_historical_year,
        )

        for supplier in sorted(self.country["exporter_name"].dropna().unique(), key=len, reverse=True):
            if supplier.lower() not in question_lower:
                continue
            supplier_row = self.country[
                (self.country["year"] == latest_year) & (self.country["exporter_name"].str.lower() == supplier.lower())
            ]
            if supplier_row.empty and latest_year != 2024:
                supplier_row = self.country[
                    (self.country["year"] == 2024) & (self.country["exporter_name"].str.lower() == supplier.lower())
                ]
            if supplier_row.empty:
                continue
            row = supplier_row.iloc[0]
            facts.append(
                f"{int(row['year'])} supplier snapshot for {supplier}: share {row['market_share_pct']:.2f}%, "
                f"imports ${row['import_value_bn']:.2f}B, dashboard risk score {row['risk_score']:.1f}/10."
            )

        return self._dedupe_facts(facts)

    def parse_substitution_upload(self, file_bytes: bytes) -> SubstitutionPreviewResponse:
        frame = pd.read_csv(io.BytesIO(file_bytes))
        normalized = frame.copy()
        normalized.columns = [column.lower().strip() for column in normalized.columns]
        return self._compute_substitution_preview_from_rows(normalized)

    def _compute_substitution_preview_from_rows(self, frame: pd.DataFrame) -> SubstitutionPreviewResponse:
        normalized = frame.copy()
        normalized.columns = [column.lower().strip() for column in normalized.columns]

        year_col = "year" if "year" in normalized.columns else None
        code_col = "hs_code" if "hs_code" in normalized.columns else None
        period_col = "period" if "period" in normalized.columns else None
        actual_col = _first_matching_column(
            list(normalized.columns),
            ("actual_value_real_2015usd_bn", "actual", "actual_value", "value_real"),
        )
        bau_col = _first_matching_column(
            list(normalized.columns),
            ("bau_forecast_real_2015usd_bn", "bau_forecast", "bau"),
        )

        if not year_col or not code_col or not actual_col:
            raise ValueError("CSV must contain year, hs_code, and an actual-value column.")

        normalized[year_col] = pd.to_numeric(normalized[year_col], errors="coerce")
        normalized[code_col] = normalized[code_col].astype(str).str.strip()
        normalized[actual_col] = pd.to_numeric(normalized[actual_col], errors="coerce")
        if bau_col:
            normalized[bau_col] = pd.to_numeric(normalized[bau_col], errors="coerce")

        if period_col:
            normalized[period_col] = normalized[period_col].astype(str).str.strip().str.lower()
            preview_rows = normalized[
                (normalized[year_col] == 2025)
                & (normalized[code_col].isin(["8542", "3818"]))
                & (normalized[period_col] == "full_year")
            ]
            if preview_rows.empty:
                preview_rows = normalized[(normalized[year_col] == 2025) & (normalized[code_col].isin(["8542", "3818"]))]
        else:
            preview_rows = normalized[(normalized[year_col] == 2025) & (normalized[code_col].isin(["8542", "3818"]))]

        bau_8542 = self._default_bau("8542")
        bau_3818 = self._default_bau("3818")
        actual_8542 = self._extract_actual(preview_rows, "8542", actual_col)
        actual_3818 = self._extract_actual(preview_rows, "3818", actual_col)

        if bau_col:
            bau_override_8542 = self._extract_actual(preview_rows, "8542", bau_col)
            bau_override_3818 = self._extract_actual(preview_rows, "3818", bau_col)
            bau_8542 = bau_override_8542 if bau_override_8542 is not None else bau_8542
            bau_3818 = bau_override_3818 if bau_override_3818 is not None else bau_3818

        if actual_8542 is None and actual_3818 is None:
            return SubstitutionPreviewResponse(
                verdict_title="Awaiting actual data",
                verdict_body="Upload a CSV to compare actual 2025 values against the BAU counterfactual.",
                verdict_level="neutral",
            )

        if (actual_8542 is not None and actual_8542 < bau_8542) and (actual_3818 is not None and actual_3818 > bau_3818):
            return SubstitutionPreviewResponse(
                verdict_title="Substitution confirmed - 2025 data",
                verdict_body=(
                    f"HS 8542 is ${bau_8542 - actual_8542:.2f}B below BAU while HS 3818 is "
                    f"${actual_3818 - bau_3818:.3f}B above BAU, which is consistent with domestic packaging activity."
                ),
                verdict_level="positive",
                hs8542_actual=_round_or_none(actual_8542, 4),
                hs3818_actual=_round_or_none(actual_3818, 4),
                hs8542_delta=_round_or_none(bau_8542 - actual_8542, 4),
                hs3818_delta=_round_or_none(actual_3818 - bau_3818, 4),
            )

        if actual_8542 is not None and actual_8542 < bau_8542:
            return SubstitutionPreviewResponse(
                verdict_title="Partial signal - finished chips below BAU",
                verdict_body=(
                    "HS 8542 is below the BAU path but HS 3818 has not yet moved decisively above BAU. "
                    "This is directionally interesting, but not enough to confirm substitution."
                ),
                verdict_level="warning",
                hs8542_actual=_round_or_none(actual_8542, 4),
                hs3818_actual=_round_or_none(actual_3818, 4),
                hs8542_delta=_round_or_none(bau_8542 - actual_8542, 4),
                hs3818_delta=_round_or_none((actual_3818 or bau_3818) - bau_3818, 4),
            )

        return SubstitutionPreviewResponse(
            verdict_title="No substitution signal detected",
            verdict_body=(
                "The uploaded values do not show the finished-chip decline plus materials rise that would indicate substitution."
            ),
            verdict_level="negative",
            hs8542_actual=_round_or_none(actual_8542, 4),
            hs3818_actual=_round_or_none(actual_3818, 4),
            hs8542_delta=_round_or_none((bau_8542 - actual_8542) if actual_8542 is not None else None, 4),
            hs3818_delta=_round_or_none((actual_3818 - bau_3818) if actual_3818 is not None else None, 4),
        )

    def _extract_actual(self, frame: pd.DataFrame, hs_code: str, column: str) -> float | None:
        rows = frame[frame["hs_code"].astype(str).str.strip() == hs_code]
        if rows.empty:
            return None
        value = rows.iloc[0][column]
        return None if pd.isna(value) else float(value)

    def _default_bau(self, hs_code: str) -> float:
        row = self.synthetic[
            (self.synthetic["year"] == 2025)
            & (self.synthetic["period"] == "full_year")
            & (self.synthetic["hs_code"] == hs_code)
        ].iloc[0]
        return float(row["bau_forecast_real_2015usd_bn"])
