import { useEffect, useMemo, useState } from "react";

import { fetchDashboard, sendChat, uploadSubstitutionCsv } from "./api";
import ChatPanel from "./components/ChatPanel";
import { ChartView, YearImportsChart, YearMixChart, YearRiskChart } from "./components/Charts";

const COMPARE_ANCHOR_YEAR = 2018;

const INITIAL_MESSAGE = {
  role: "assistant",
  content:
    "I can answer questions about the historical data, supplier risk, substitution logic, and the ARIMAX baseline. Pick a chart context, choose a compare year in Year Analysis, or ask directly from the active tab.",
  citations: [],
  exactFacts: []
};

function getSpanClass(index, total) {
  return total === 1 || (total % 2 === 1 && index === total - 1) ? "panel-span-2" : "";
}

function classForTone(tone) {
  return tone ? `kpi-${tone}` : "kpi-muted";
}

function verdictClass(level) {
  if (level === "positive") return "verdict-positive";
  if (level === "warning") return "verdict-warning";
  if (level === "negative") return "verdict-negative";
  return "verdict-neutral";
}

function overwriteActual(data, actualValue) {
  if (actualValue === null || actualValue === undefined) {
    return data;
  }
  return data.map((row) => (row.year === 2025 ? { ...row, actual: actualValue } : row));
}

function formatBillions(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return `$${Number(value).toFixed(digits)}B`;
}

function formatPercent(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return `${Number(value).toFixed(digits)}%`;
}

function formatSignedBillions(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "n/a";
  }
  return `${value >= 0 ? "+" : "-"}$${Math.abs(Number(value)).toFixed(digits)}B`;
}

function formatSignedPoints(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "n/a";
  }
  return `${Number(value).toFixed(digits).startsWith("-") ? "" : "+"}${Number(value).toFixed(digits)} pp`;
}

function formatSignedNumber(value, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "n/a";
  }
  return `${Number(value).toFixed(digits).startsWith("-") ? "" : "+"}${Number(value).toFixed(digits)}`;
}

function formatSignedCount(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "n/a";
  }
  return `${value >= 0 ? "+" : ""}${Number(value).toFixed(0)}`;
}

function pickCompareYear(availableYears, selectedYear, preferredYear = COMPARE_ANCHOR_YEAR) {
  const candidates = availableYears.filter((year) => year !== selectedYear);
  if (!candidates.length) {
    return null;
  }
  if (preferredYear && candidates.includes(preferredYear)) {
    return preferredYear;
  }
  const earlier = candidates.filter((year) => year < selectedYear);
  if (earlier.length) {
    return earlier[earlier.length - 1];
  }
  return candidates[0];
}

function toneForDirectionalDelta(value, desiredDirection = "neutral") {
  if (value === null || value === undefined || Math.abs(Number(value)) < 0.005) {
    return "neutral";
  }
  if (desiredDirection === "higher-is-better") {
    return value > 0 ? "positive" : "warning";
  }
  if (desiredDirection === "lower-is-better") {
    return value < 0 ? "positive" : "warning";
  }
  return value > 0 ? "info" : "neutral";
}

function describeDirectionalMove(value, higherLabel, lowerLabel, flatLabel) {
  if (value === null || value === undefined || Math.abs(Number(value)) < 0.005) {
    return flatLabel;
  }
  return value > 0 ? higherLabel : lowerLabel;
}

function buildYearComparison(selectedYear, current, compareYear, compare) {
  if (!current) {
    return null;
  }

  if (!compare || !compareYear || compareYear === selectedYear) {
    return {
      enabled: false,
      headline: `Year ${selectedYear}`,
      summaryLead: `${selectedYear} is the selected reference year, with imports anchored at ${formatBillions(current.nominalBill)} and supplier concentration still elevated.`,
      summaryBody: `China share is ${formatPercent(current.chinaShare)}, HHI is ${current.hhi.toFixed(3)}, and ${current.topExporter} remains the top exporter in the basket.`,
      contextLine: `China share ${formatPercent(current.chinaShare)} | Supplier HHI ${current.hhi.toFixed(3)} | HS 8542 share ${formatPercent(current.hs8542Share)}`
    };
  }

  const nominalDelta = current.nominalBill - compare.nominalBill;
  const realDelta = current.realBill - compare.realBill;
  const chinaDelta = current.chinaShare - compare.chinaShare;
  const hhiDelta = current.hhi - compare.hhi;
  const hs8542Delta = current.hs8542Share - compare.hs8542Share;
  const concentrationLabel = describeDirectionalMove(hhiDelta, "more concentrated", "less concentrated", "similarly concentrated");
  const scaleLabel = describeDirectionalMove(nominalDelta, "higher-import", "lower-import", "similar-import");
  const chinaLabel = describeDirectionalMove(chinaDelta, "China share up", "China share down", "China share flat");
  const exporterLabel =
    current.topExporter === compare.topExporter
      ? `top exporter unchanged at ${current.topExporter}`
      : `top exporter shifts from ${compare.topExporter} to ${current.topExporter}`;

  return {
    enabled: true,
    headline: `${selectedYear} vs ${compareYear}`,
    summaryLead: `${selectedYear} is a ${scaleLabel}, ${concentrationLabel} year than ${compareYear}, with ${chinaLabel} and ${exporterLabel}.`,
    summaryBody: `Nominal imports are ${formatSignedBillions(nominalDelta)} and real imports are ${formatSignedBillions(realDelta)} versus ${compareYear}; HHI is ${formatSignedNumber(hhiDelta)} and China share is ${formatSignedPoints(chinaDelta)}.`,
    contextLine: `${selectedYear} vs ${compareYear}: nominal ${formatSignedBillions(nominalDelta)} | China share ${formatSignedPoints(chinaDelta)} | HHI ${formatSignedNumber(hhiDelta)}`
  };
}

function buildYearMetricCards(selectedYear, current, compareYear, compare) {
  if (!current) {
    return [];
  }

  const baselineYear = compareYear ?? selectedYear;
  const baseline = compare && compareYear ? compare : current;
  const nominalDelta = current.nominalBill - baseline.nominalBill;
  const realDelta = current.realBill - baseline.realBill;
  const chinaDelta = current.chinaShare - baseline.chinaShare;
  const hhiDelta = current.hhi - baseline.hhi;
  const hs8542Delta = current.hs8542Share - baseline.hs8542Share;
  const hs3818Delta = current.hs3818Share - baseline.hs3818Share;
  const exporterChangeCount = current.topExporter === baseline.topExporter ? 0 : 1;

  return [
    {
      label: "Nominal imports",
      primaryValue: formatBillions(current.nominalBill),
      secondaryValue: `${baselineYear}: ${formatBillions(baseline.nominalBill)}`,
      delta: formatSignedBillions(nominalDelta),
      deltaTone: toneForDirectionalDelta(nominalDelta),
      tone: "green"
    },
    {
      label: "Real imports",
      primaryValue: formatBillions(current.realBill),
      secondaryValue: `${baselineYear}: ${formatBillions(baseline.realBill)}`,
      delta: formatSignedBillions(realDelta),
      deltaTone: toneForDirectionalDelta(realDelta),
      tone: "blue"
    },
    {
      label: "China share",
      primaryValue: formatPercent(current.chinaShare),
      secondaryValue: `${baselineYear}: ${formatPercent(baseline.chinaShare)}`,
      delta: formatSignedPoints(chinaDelta),
      deltaTone: toneForDirectionalDelta(chinaDelta, "lower-is-better"),
      tone: "red"
    },
    {
      label: "HHI",
      primaryValue: current.hhi.toFixed(3),
      secondaryValue: `${baselineYear}: ${baseline.hhi.toFixed(3)}`,
      delta: formatSignedNumber(hhiDelta),
      deltaTone: toneForDirectionalDelta(hhiDelta, "lower-is-better"),
      tone: "amber"
    },
    {
      label: "HS 8542 share",
      primaryValue: formatPercent(current.hs8542Share),
      secondaryValue: `${baselineYear}: ${formatPercent(baseline.hs8542Share)}`,
      delta: formatSignedPoints(hs8542Delta),
      deltaTone: toneForDirectionalDelta(hs8542Delta, "lower-is-better"),
      tone: "green"
    },
    {
      label: "HS 3818 share",
      primaryValue: formatPercent(current.hs3818Share),
      secondaryValue: `${baselineYear}: ${formatPercent(baseline.hs3818Share)}`,
      delta: formatSignedPoints(hs3818Delta),
      deltaTone: toneForDirectionalDelta(hs3818Delta, "higher-is-better"),
      tone: "blue"
    },
    {
      label: "Top exporter change",
      primaryValue: current.topExporter,
      secondaryValue: `${baselineYear}: ${baseline.topExporter}`,
      delta: `${formatSignedCount(exporterChangeCount)} change${exporterChangeCount === 1 ? "" : "s"}`,
      deltaTone: exporterChangeCount ? "warning" : "neutral",
      tone: "muted"
    }
  ];
}

function kpiCard(kpi) {
  return (
    <article key={kpi.label} className={`kpi-card ${classForTone(kpi.tone)}`}>
      <div className="kpi-label">{kpi.label}</div>
      <div className="kpi-value">{kpi.value}</div>
      <div className="kpi-delta">{kpi.delta}</div>
    </article>
  );
}

function YearMetricCard({ metric }) {
  return (
    <article className={`year-metric-card year-metric-${metric.tone}`}>
      <div className="year-metric-top">
        <span className="kpi-label">{metric.label}</span>
        <span className={`delta-pill delta-${metric.deltaTone}`}>{metric.delta}</span>
      </div>
      <div className="year-metric-value">{metric.primaryValue}</div>
      <div className="year-metric-sub">{metric.secondaryValue}</div>
    </article>
  );
}

function ChartPanel({ chart, children, onAsk, className = "" }) {
  return (
    <section className={`panel ${className}`.trim()}>
      <div className="compact-head">
        <div>
          <div className="panel-title">{chart.title}</div>
          <div className="panel-sub">{chart.subtitle}</div>
        </div>
        <button type="button" className="panel-ask" onClick={() => onAsk(chart.id, chart.title)}>
          Ask AI
        </button>
      </div>
      <div className="panel-divider" />
      <div className="chart-wrap">{children}</div>
      <div className="insight-box">
        <span className="insight-label">What this means</span>
        <p>{chart.insight}</p>
      </div>
    </section>
  );
}

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedYear, setSelectedYear] = useState(2024);
  const [compareYear, setCompareYear] = useState(null);
  const [focusedChartId, setFocusedChartId] = useState(null);
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [draft, setDraft] = useState("");
  const [chatPending, setChatPending] = useState(false);
  const [chatError, setChatError] = useState("");
  const [substitutionPreview, setSubstitutionPreview] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const payload = await fetchDashboard();
        setDashboard(payload);
        setSelectedYear(payload.yearAnalysis.defaultYear);
        setCompareYear(payload.yearAnalysis.defaultCompareYear ?? null);
        setSubstitutionPreview(payload.substitutionTracker.preview);
      } catch (error) {
        setLoadError(error.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const availableYears = dashboard?.yearAnalysis?.availableYears || [];

  useEffect(() => {
    if (!dashboard || !availableYears.length) {
      return;
    }
    setCompareYear((current) => {
      if (current && current !== selectedYear && availableYears.includes(current)) {
        return current;
      }
      return pickCompareYear(availableYears, selectedYear, dashboard.yearAnalysis.defaultCompareYear) ?? selectedYear;
    });
  }, [availableYears, dashboard, selectedYear]);

  const activeTabLabel = useMemo(() => {
    if (!dashboard) return "Loading";
    return dashboard.tabs.find((tab) => tab.id === activeTab)?.label || "Overview";
  }, [dashboard, activeTab]);

  const currentYearDetail = dashboard?.yearAnalysis?.yearDetails?.[String(selectedYear)];
  const activeCompareYear = compareYear !== selectedYear ? compareYear : null;
  const compareYearDetail = activeCompareYear
    ? dashboard?.yearAnalysis?.yearDetails?.[String(activeCompareYear)]
    : null;
  const isCompareMode = Boolean(activeCompareYear && compareYearDetail);

  const importCharts = useMemo(() => Object.values(dashboard?.importAnalysis?.charts || {}), [dashboard]);
  const riskCharts = useMemo(() => Object.values(dashboard?.supplierRisk?.charts || {}), [dashboard]);

  const substitutionCharts = useMemo(() => {
    if (!dashboard) return null;
    return {
      hs8542: {
        ...dashboard.substitutionTracker.charts.hs8542,
        data: overwriteActual(dashboard.substitutionTracker.charts.hs8542.data, substitutionPreview?.hs8542_actual)
      },
      hs3818: {
        ...dashboard.substitutionTracker.charts.hs3818,
        data: overwriteActual(dashboard.substitutionTracker.charts.hs3818.data, substitutionPreview?.hs3818_actual)
      }
    };
  }, [dashboard, substitutionPreview]);

  const yearComparison = useMemo(
    () => buildYearComparison(selectedYear, currentYearDetail, activeCompareYear, compareYearDetail),
    [activeCompareYear, compareYearDetail, currentYearDetail, selectedYear]
  );

  const yearMetricCards = useMemo(
    () => buildYearMetricCards(selectedYear, currentYearDetail, activeCompareYear, compareYearDetail),
    [activeCompareYear, compareYearDetail, currentYearDetail, selectedYear]
  );

  const yearMetaStats = useMemo(() => {
    if (!currentYearDetail) {
      return [];
    }
    if (!isCompareMode || !compareYearDetail) {
      return [
        {
          label: "Top exporter",
          value: currentYearDetail.topExporter,
          note: "Largest supplier node"
        },
        {
          label: "Top 3 share",
          value: formatPercent(currentYearDetail.top3Share),
          note: "Supplier concentration"
        },
        {
          label: "Exporters",
          value: currentYearDetail.numExporters,
          note: "Countries in basket"
        },
        {
          label: "Real YoY",
          value: formatPercent(currentYearDetail.yoyReal),
          note: "Annual change"
        }
      ];
    }
    return [
      {
        label: "Top exporter",
        value:
          currentYearDetail.topExporter === compareYearDetail.topExporter
            ? `${currentYearDetail.topExporter} in both years`
            : `${compareYearDetail.topExporter} -> ${currentYearDetail.topExporter}`,
        note: "Lead supplier"
      },
      {
        label: "Nominal change",
        value: formatSignedBillions(currentYearDetail.nominalBill - compareYearDetail.nominalBill),
        note: `Scale versus ${activeCompareYear}`
      },
      {
        label: "China share",
        value: formatSignedPoints(currentYearDetail.chinaShare - compareYearDetail.chinaShare),
        note: `Dependency shift versus ${activeCompareYear}`
      },
      {
        label: "HHI change",
        value: formatSignedNumber(currentYearDetail.hhi - compareYearDetail.hhi),
        note: `Concentration versus ${activeCompareYear}`
      }
    ];
  }, [activeCompareYear, compareYearDetail, currentYearDetail, isCompareMode]);

  const compareYearOptions = useMemo(() => availableYears, [availableYears]);

  const chatSuggestions = useMemo(() => {
    if (!dashboard) {
      return [];
    }
    const baseSuggestions = dashboard.chat.suggestions || [];
    if (activeTab === "year" && isCompareMode && activeCompareYear) {
      const comparePrompt = `Compare ${activeCompareYear} and ${selectedYear}.`;
      return [comparePrompt, ...baseSuggestions.filter((item) => item !== comparePrompt)];
    }
    return baseSuggestions;
  }, [activeCompareYear, activeTab, dashboard, isCompareMode, selectedYear]);

  const chatContextLabel = useMemo(() => {
    const yearPart =
      activeTab === "year"
        ? isCompareMode && activeCompareYear
          ? `Year ${selectedYear} vs ${activeCompareYear}`
          : `Year ${selectedYear}`
        : activeTabLabel;
    const chartPart = focusedChartId ? ` | ${focusedChartId}` : "";
    return `${yearPart}${chartPart}`;
  }, [activeCompareYear, activeTab, activeTabLabel, focusedChartId, isCompareMode, selectedYear]);

  async function handleChatSubmit(text) {
    const question = text.trim();
    if (!question || !dashboard) {
      return;
    }

    setChatPending(true);
    setChatError("");
    setDraft("");
    setMessages((current) => [...current, { role: "user", content: question }]);

    try {
      const conversation = messages
        .filter((message) => message.role === "user" || message.role === "assistant")
        .map((message) => ({ role: message.role, content: message.content }));

      const response = await sendChat({
        question,
        active_tab: activeTab,
        chart_id: focusedChartId,
        selected_year: activeTab === "year" ? selectedYear : null,
        compare_year: activeTab === "year" && isCompareMode ? activeCompareYear : null,
        conversation
      });

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          exactFacts: response.exact_facts,
          model: response.model
        }
      ]);
    } catch (error) {
      setChatError(error.message);
    } finally {
      setChatPending(false);
    }
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    try {
      const preview = await uploadSubstitutionCsv(file);
      setSubstitutionPreview(preview);
      setUploadedFileName(file.name);
    } catch (error) {
      setChatError(error.message);
    }
  }

  function askChart(chartId, title) {
    setFocusedChartId(chartId);

    if (activeTab === "year" && isCompareMode && activeCompareYear) {
      setDraft(`Compare ${activeCompareYear} and ${selectedYear} using "${title}". What changed most and why?`);
      return;
    }

    if (activeTab === "year") {
      setDraft(`Explain what stands out in ${selectedYear} from "${title}" and why it matters.`);
      return;
    }

    setDraft(`Explain the main takeaway from "${title}" and how I should interpret it.`);
  }

  if (loading) {
    return <div className="loading-state">Loading the React dashboard and retrieval context...</div>;
  }

  if (loadError || !dashboard) {
    return <div className="loading-state">Could not load dashboard: {loadError}</div>;
  }

  return (
    <div className="app-shell">
      <header className="header">
        <div className="header-top">
          <div className="logo-wrap">
            <div className="logo-icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M10 2L10 18M6 6L10 2L14 6M6 14L10 18L14 14" stroke="#86efac" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                <circle cx="10" cy="10" r="2.5" fill="#4ade80" />
              </svg>
            </div>
            <div>
              <div className="logo-title">{dashboard.meta.title}</div>
              <div className="logo-sub">{dashboard.meta.subtitle}</div>
            </div>
          </div>
          <div className="header-meta">
            {dashboard.meta.chips.map((chip) => (
              <span key={chip} className="meta-chip">
                {chip}
              </span>
            ))}
          </div>
        </div>
        <div className="tab-bar">
          {dashboard.tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`tab-btn ${tab.id === activeTab ? "active" : ""}`}
              onClick={() => {
                setActiveTab(tab.id);
                setFocusedChartId(null);
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      <div className="breadcrumb">
        <span className="bc-accent">{dashboard.meta.title}</span>
        <span>/</span>
        <span>{activeTabLabel}</span>
        <span className="bc-right">Groq answers with local retrieval over the report, chart notes, and processed CSVs</span>
      </div>

      <div className="workspace">
        <main className="main">
          {activeTab === "overview" ? (
            <>
              <section className="hero-strip">
                <div>
                  <div className="hero-eyebrow">{dashboard.overview.hero.eyebrow}</div>
                  <h1>{dashboard.overview.hero.title}</h1>
                  <p className="hero-text">{dashboard.overview.hero.description}</p>
                  <div className="hero-pills">
                    {dashboard.overview.hero.pills.map((pill) => (
                      <span key={pill} className="meta-chip hero-pill">
                        {pill}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="hero-side">
                  <div className="hero-stats">
                    {dashboard.overview.hero.stats.map((stat) => (
                      <div key={stat.label} className="hero-stat">
                        <div className="hero-stat-label">{stat.label}</div>
                        <div className="hero-stat-value">{stat.value}</div>
                        <div className="hero-stat-copy">{stat.copy}</div>
                      </div>
                    ))}
                  </div>
                  <div className="timeline-box">
                    <div className="panel-title">Shock map</div>
                    <div className="panel-sub">Crisis windows change the level, but not the long-run dependence story.</div>
                    <ul className="timeline-list">
                      {dashboard.overview.hero.timeline.map((item) => (
                        <li key={item.year}>
                          <span className="timeline-year">{item.year}</span>
                          <span className="timeline-copy">{item.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>

              <section className="panel">
                <div className="section-head">
                  <div>
                    <div className="section-tag">Key reads</div>
                    <h2>What matters most in the historical record</h2>
                  </div>
                  <span className="section-badge">Historical view through 2024</span>
                </div>
                <ul className="key-insights-list">
                  {dashboard.overview.insights.map((insight) => (
                    <li key={insight.title}>
                      <span className="key-kicker">{insight.kicker}</span>
                      <strong>{insight.title}</strong>
                      <span>{insight.copy}</span>
                    </li>
                  ))}
                </ul>
              </section>

              <section className="section-block">
                <div className="section-head">
                  <div>
                    <div className="section-tag">Macro Trends</div>
                    <h2>Scale first, then acceleration</h2>
                    <p>The first question is still whether imports are leveling off. They are not.</p>
                  </div>
                  <span className="section-badge">1995-2027</span>
                </div>
                <div className="analytics-grid">
                  <ChartPanel chart={dashboard.overview.charts.trajectory} onAsk={askChart}>
                    <ChartView chartId="trajectory" data={dashboard.overview.charts.trajectory.data} />
                  </ChartPanel>
                  <ChartPanel chart={dashboard.overview.charts.acceleration} onAsk={askChart}>
                    <ChartView chartId="acceleration" data={dashboard.overview.charts.acceleration.data} />
                  </ChartPanel>
                </div>
              </section>

              <section className="section-block">
                <div className="section-head">
                  <div>
                    <div className="section-tag">Supply Chain Structure</div>
                    <h2>Concentration still sits in a narrow corridor</h2>
                    <p>Even when the supplier count grows, value concentration remains stubbornly high.</p>
                  </div>
                  <span className="section-badge">2024 snapshot + long-run shift</span>
                </div>
                <div className="analytics-grid">
                  <ChartPanel chart={dashboard.overview.charts.supplierBreakdown} onAsk={askChart}>
                    <ChartView chartId="supplierBreakdown" data={dashboard.overview.charts.supplierBreakdown.data} />
                  </ChartPanel>
                  <ChartPanel chart={dashboard.overview.charts.shareTrends} onAsk={askChart}>
                    <ChartView chartId="shareTrends" data={dashboard.overview.charts.shareTrends.data} />
                  </ChartPanel>
                </div>
              </section>

              <section className="section-block">
                <div className="section-head">
                  <div>
                    <div className="section-tag">Risk Analysis</div>
                    <h2>Dependence and concentration reinforce each other</h2>
                    <p>The risk story becomes clearer once China share and HHI are seen together instead of separately.</p>
                  </div>
                  <span className="section-badge">Exposure profile</span>
                </div>
                <div className="analytics-grid">
                  <ChartPanel chart={dashboard.overview.charts.riskCorrelation} onAsk={askChart} className="panel-span-2">
                    <ChartView chartId="riskCorrelation" data={dashboard.overview.charts.riskCorrelation.data} />
                  </ChartPanel>
                </div>
              </section>
            </>
          ) : null}

          {activeTab === "import" ? (
            <>
              <section className="page-band">
                <div>
                  <div className="section-tag">Import Analysis</div>
                  <h2>Product mix, growth, and volatility in one view</h2>
                  <p>
                    This page reads the basket structurally: what India is importing, how fast it is expanding, and how
                    unstable that growth path has become.
                  </p>
                </div>
                <div className="page-band-note">Three core diagnostics</div>
              </section>
              <section className="kpi-strip">{dashboard.importAnalysis.kpis.map((kpi) => kpiCard(kpi))}</section>
              <div className="analytics-grid">
                {importCharts.map((chart, index) => (
                  <ChartPanel key={chart.id} chart={chart} onAsk={askChart} className={getSpanClass(index, importCharts.length)}>
                    <ChartView chartId={chart.id} data={chart.data} />
                  </ChartPanel>
                ))}
              </div>
            </>
          ) : null}

          {activeTab === "year" && currentYearDetail ? (
            <>
              <section className="page-band">
                <div>
                  <div className="section-tag">Year Analysis</div>
                  <h2>Choose one year or compare two side-by-side</h2>
                  <p>
                    Use this view as an operating readout: scale, supplier structure, concentration, and how one year or a
                    comparison pair sits inside the full historical curve.
                  </p>
                </div>
                <div className="page-band-note">
                  {isCompareMode && activeCompareYear ? `Comparing ${selectedYear} vs ${activeCompareYear}` : "Single-year view"}
                </div>
              </section>

              <section className="year-workbench">
                <section className="panel year-context-panel">
                  <div className="compact-head">
                    <div>
                      <div className="panel-title">{dashboard.yearAnalysis.contextChart.title}</div>
                      <div className="panel-sub">
                        {isCompareMode
                          ? "Use the long-run curve first, then read the deltas in the side rail."
                          : dashboard.yearAnalysis.contextChart.subtitle}
                      </div>
                    </div>
                    <button type="button" className="panel-ask" onClick={() => askChart("yearContext", `Year ${selectedYear} historical context`)}>
                      Ask AI
                    </button>
                  </div>
                  <div className="year-context-toolbar">
                    <div className="chart-context-pills">
                      <span className="context-pill context-pill-focus">Focus {selectedYear}</span>
                      {isCompareMode && activeCompareYear ? (
                        <span className="context-pill context-pill-compare">Compare {activeCompareYear}</span>
                      ) : null}
                    </div>
                    <div className="year-context-note">{yearComparison?.contextLine}</div>
                  </div>
                  <div className="panel-divider" />
                  <div className="chart-wrap chart-wrap-year-context">
                    <ChartView
                      chartId="yearContext"
                      data={dashboard.yearAnalysis.contextChart.data}
                      selectedYear={selectedYear}
                      compareYear={activeCompareYear}
                    />
                  </div>
                </section>

                <section className="panel year-rail">
                  <div className="year-rail-head">
                    <div className="panel-title">{yearComparison?.headline}</div>
                    <div className="panel-sub">
                      {isCompareMode
                        ? "Choose the pair, read the conclusion, then scan the quick context shifts."
                        : "Pick a reference year and read the structural profile before drilling into the smaller charts."}
                    </div>
                  </div>

                  <div className="year-control-grid">
                    <div className="control-group">
                      <label className="control-label" htmlFor="year-select">
                        Primary year
                      </label>
                      <select
                        id="year-select"
                        className="select-input"
                        value={selectedYear}
                        onChange={(event) => setSelectedYear(Number(event.target.value))}
                      >
                        {availableYears.map((year) => (
                          <option key={year} value={year}>
                            {year}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="control-group">
                      <label className="control-label" htmlFor="compare-year-select">
                        Compare year
                      </label>
                      <select
                        id="compare-year-select"
                        className="select-input"
                        value={compareYear ?? selectedYear}
                        onChange={(event) => setCompareYear(Number(event.target.value))}
                      >
                        {compareYearOptions.map((year) => (
                          <option key={year} value={year}>
                            {year}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="year-chip-row">
                    <span className="year-chip">Focus {selectedYear}</span>
                    <span className="year-chip year-chip-compare">{isCompareMode && activeCompareYear ? `Compare ${activeCompareYear}` : "Single-year read"}</span>
                  </div>

                  <div className="year-summary-callout year-summary-rail">
                    <p>{yearComparison?.summaryLead}</p>
                    <div className="year-callout-note">{yearComparison?.summaryBody}</div>
                  </div>

                  <div className="year-stat-row year-stat-row-compact">
                    {yearMetaStats.map((stat) => (
                      <div key={stat.label} className="meta-stat year-meta-stat">
                        <span>{stat.label}</span>
                        <strong>{stat.value}</strong>
                        <div className="meta-stat-note">{stat.note}</div>
                      </div>
                    ))}
                  </div>
                </section>
              </section>

              <section className="panel year-kpi-panel">
                <div className="compact-head">
                  <div>
                    <div className="panel-title">{isCompareMode ? "Comparison metrics" : "Selected year metrics"}</div>
                    <div className="panel-sub">
                      {isCompareMode
                        ? "Selected year first, baseline second, signed delta on the right."
                        : "The quantities you should usually cite before asking the model for interpretation."}
                    </div>
                  </div>
                </div>
                <div className="panel-divider" />
                <div className="year-metric-grid">
                  {yearMetricCards.map((metric) => (
                    <YearMetricCard key={metric.label} metric={metric} />
                  ))}
                </div>
              </section>

              <section className="year-detail-grid">
                <section className="panel">
                  <div className="panel-title">{isCompareMode ? "Import bills" : "Selected year imports"}</div>
                  <div className="panel-sub">
                    {isCompareMode ? "Nominal and real imports shown side-by-side across the selected pair" : "Nominal versus real bill for the selected year"}
                  </div>
                  <div className="panel-divider" />
                  <div className="chart-wrap-sm chart-wrap">
                    <YearImportsChart
                      detail={currentYearDetail}
                      compareDetail={compareYearDetail}
                      selectedYear={selectedYear}
                      compareYear={activeCompareYear}
                    />
                  </div>
                </section>

                <section className="panel">
                  <div className="panel-title">{isCompareMode ? "Product mix shares" : "Selected year product mix"}</div>
                  <div className="panel-sub">
                    {isCompareMode ? "HS 8542 and HS 3818 share split for both years" : "HS 8542 still overwhelms HS 3818"}
                  </div>
                  <div className="panel-divider" />
                  <div className="chart-wrap-sm chart-wrap">
                    <YearMixChart
                      detail={currentYearDetail}
                      compareDetail={compareYearDetail}
                      selectedYear={selectedYear}
                      compareYear={activeCompareYear}
                    />
                  </div>
                </section>

                <section className="panel">
                  <div className="panel-title">{isCompareMode ? "Risk mix comparison" : "Selected year risk mix"}</div>
                  <div className="panel-sub">
                    {isCompareMode
                      ? "China share, non-China share, and HHI x100 side-by-side across both years"
                      : "China share, non-China share, and HHI x100 in one view"}
                  </div>
                  <div className="panel-divider" />
                  <div className="chart-wrap-sm chart-wrap">
                    <YearRiskChart
                      detail={currentYearDetail}
                      compareDetail={compareYearDetail}
                      selectedYear={selectedYear}
                      compareYear={activeCompareYear}
                    />
                  </div>
                </section>
              </section>
            </>
          ) : null}

          {activeTab === "subst" && substitutionCharts ? (
            <>
              <section className="upload-panel">
                <div className="panel-title">{dashboard.substitutionTracker.uploadTitle}</div>
                <div className="panel-sub">{dashboard.substitutionTracker.uploadDescription}</div>
                <label className="upload-zone" htmlFor="csv-file">
                  <span className="upload-icon">CSV</span>
                  <div className="upload-title">Drop or choose a file</div>
                  <div className="upload-sub">{dashboard.substitutionTracker.uploadFormat}</div>
                  <span className="upload-btn">Choose CSV</span>
                </label>
                <input id="csv-file" type="file" accept=".csv" onChange={handleUpload} />
                {uploadedFileName ? (
                  <div className="file-loaded">
                    Loaded: <span className="fl-name">{uploadedFileName}</span>
                  </div>
                ) : null}
              </section>

              <section className={`verdict-banner ${verdictClass(substitutionPreview?.verdict_level)}`}>
                <div className="verdict-header">
                  <div className="verdict-dot" />
                  <div className="verdict-title">{substitutionPreview?.verdict_title}</div>
                </div>
                <div className="verdict-body">{substitutionPreview?.verdict_body}</div>
              </section>

              <div className="kpi-strip">
                {[
                  {
                    label: "Actual HS 8542",
                    value: substitutionPreview?.hs8542_actual ? `$${substitutionPreview.hs8542_actual}B` : "Pending",
                    delta: substitutionPreview?.hs8542_delta ? `${substitutionPreview.hs8542_delta}B below BAU` : "Awaiting upload",
                    tone: "green"
                  },
                  {
                    label: "Actual HS 3818",
                    value: substitutionPreview?.hs3818_actual ? `$${substitutionPreview.hs3818_actual}B` : "Pending",
                    delta: substitutionPreview?.hs3818_delta ? `${substitutionPreview.hs3818_delta}B above BAU` : "Awaiting upload",
                    tone: "blue"
                  }
                ].map((kpi) => kpiCard(kpi))}
              </div>

              <div className="analytics-grid">
                <ChartPanel chart={substitutionCharts.hs8542} onAsk={askChart}>
                  <ChartView chartId={substitutionCharts.hs8542.id} data={substitutionCharts.hs8542.data} />
                </ChartPanel>
                <ChartPanel chart={substitutionCharts.hs3818} onAsk={askChart}>
                  <ChartView chartId={substitutionCharts.hs3818.id} data={substitutionCharts.hs3818.data} />
                </ChartPanel>
              </div>
            </>
          ) : null}

          {activeTab === "risk" ? (
            <>
              <section className="page-band">
                <div>
                  <div className="section-tag">Supplier Risk</div>
                  <h2>Where dependence becomes vulnerability</h2>
                  <p>
                    The risk page compresses corridor exposure, concentration, and the supplier matrix into a single
                    monitoring view.
                  </p>
                </div>
                <div className="page-band-note">2024 snapshot + long-run corridor</div>
              </section>
              <section className="kpi-strip">{dashboard.supplierRisk.kpis.map((kpi) => kpiCard(kpi))}</section>
              <ChartPanel chart={dashboard.supplierRisk.charts.riskCorridor} onAsk={askChart}>
                <ChartView chartId="riskCorridor" data={dashboard.supplierRisk.charts.riskCorridor.data} />
              </ChartPanel>
              <div className="analytics-grid">
                {riskCharts
                  .filter((chart) => chart.id !== "riskCorridor")
                  .map((chart, index, list) => (
                    <ChartPanel key={chart.id} chart={chart} onAsk={askChart} className={getSpanClass(index, list.length)}>
                      <ChartView chartId={chart.id} data={chart.data} />
                    </ChartPanel>
                  ))}
              </div>
              <section className="panel">
                <div className="panel-title">Supplier risk assessment matrix</div>
                <div className="panel-sub">2024 snapshot by country, share, value, and dashboard risk score</div>
                <div className="panel-divider" />
                <div className="table-wrap">
                  <table className="risk-table">
                    <thead>
                      <tr>
                        <th>Country</th>
                        <th>Market share</th>
                        <th>Import value</th>
                        <th>Risk</th>
                        <th>Level</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard.supplierRisk.table.map((row) => (
                        <tr key={row.country}>
                          <td>{row.country}</td>
                          <td>{row.share}%</td>
                          <td>${row.value}B</td>
                          <td>{row.risk}/10</td>
                          <td>
                            <span className={`tag tag-${row.level.toLowerCase()}`}>{row.level}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          ) : null}
        </main>
        <aside className="chat-rail">
          <ChatPanel
            className="chat-panel-embedded"
            messages={messages}
            draft={draft}
            setDraft={setDraft}
            onSubmit={handleChatSubmit}
            pending={chatPending}
            suggestions={chatSuggestions}
            contextLabel={chatContextLabel}
            error={chatError}
          />
        </aside>
      </div>

      <footer className="footer">
        <span>{dashboard.meta.footer.left}</span>
        <span>{dashboard.meta.footer.right}</span>
      </footer>
    </div>
  );
}

export default App;
