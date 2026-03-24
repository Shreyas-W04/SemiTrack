import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis
} from "recharts";

const COLORS = {
  accent: "#165e35",
  accent2: "#229656",
  blue: "#0b6d8d",
  amber: "#b86e0b",
  red: "#9f2525",
  danger: "#9f2525",
  success: "#1f8c4f",
  muted: "#55705d",
  grid: "#d3e4cd",
  text: "#17301d"
};

const tooltipStyle = {
  background: "rgba(255,255,255,0.98)",
  border: "1px solid #d3e4cd",
  borderRadius: "14px",
  boxShadow: "0 12px 30px rgba(19,33,18,.12)"
};

function shortBillions(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  const numeric = Number(value);
  return `$${numeric >= 1 ? numeric.toFixed(2) : numeric.toFixed(3)}B`;
}

function shortPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return `${Number(value).toFixed(1)}%`;
}

function numberTick(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "";
  }
  return Number(value).toFixed(1);
}

function ChartTooltip({ active, payload, label, formatter }) {
  if (!active || !payload?.length) {
    return null;
  }
  const heading = label ?? payload[0]?.payload?.year ?? payload[0]?.name ?? "Details";
  return (
    <div style={tooltipStyle}>
      <div style={{ padding: "12px 14px" }}>
        <div style={{ fontWeight: 700, color: COLORS.text, marginBottom: 8 }}>{heading}</div>
        {payload.map((entry) => (
          <div
            key={`${entry.dataKey}-${entry.name}`}
            style={{ display: "flex", gap: 10, alignItems: "center", fontSize: 12, color: COLORS.muted, marginTop: 4 }}
          >
            <span style={{ width: 8, height: 8, borderRadius: 999, background: entry.color }} />
            <span>{entry.name}</span>
            <strong style={{ color: COLORS.text }}>{formatter ? formatter(entry.value, entry.name, entry.payload) : entry.value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function commonAxisProps() {
  return {
    tick: { fill: COLORS.muted, fontSize: 11 },
    axisLine: false,
    tickLine: false
  };
}

export function ChartView({ chartId, data, selectedYear, compareYear }) {
  switch (chartId) {
    case "trajectory":
      return <TrajectoryChart data={data} />;
    case "acceleration":
      return <AccelerationChart data={data} />;
    case "supplierBreakdown":
      return <SupplierBreakdownChart data={data} />;
    case "shareTrends":
      return <ShareTrendChart data={data} />;
    case "riskCorrelation":
      return <RiskScatterChart data={data} />;
    case "productMix":
      return <ProductMixChart data={data} />;
    case "yoyGrowth":
      return <GrowthChart data={data} />;
    case "volatility":
      return <VolatilityChart data={data} />;
    case "riskCorridor":
      return <RiskCorridorChart data={data} />;
    case "riskScore":
      return <RiskBarChart data={data} dataKey="riskScore" name="Risk score" domain={[0, 10]} />;
    case "hhi":
      return <RiskBarChart data={data} dataKey="hhi" name="HHI" domain={[0, 0.4]} />;
    case "yearContext":
      return <YearContextChart data={data} selectedYear={selectedYear} compareYear={compareYear} />;
    case "substitutionHs8542":
      return <SubstitutionChart data={data} formatter={shortBillions} />;
    case "substitutionHs3818":
      return <SubstitutionChart data={data} formatter={shortBillions} />;
    default:
      return <div className="chart-empty">Chart unavailable.</div>;
  }
}

function TrajectoryChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="year" {...commonAxisProps()} />
        <YAxis {...commonAxisProps()} tickFormatter={shortBillions} />
        <Tooltip content={<ChartTooltip formatter={shortBillions} />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="real" name="Real imports" stroke={COLORS.accent} strokeWidth={2.6} dot={false} />
        <Line type="monotone" dataKey="nominal" name="Nominal imports" stroke={COLORS.accent2} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="forecast" name="ARIMAX forecast" stroke={COLORS.amber} strokeWidth={2.2} dot={false} strokeDasharray="7 5" />
        <Line type="monotone" dataKey="forecastLower" name="Forecast lower" stroke="#d8b06a" strokeWidth={1.2} dot={false} />
        <Line type="monotone" dataKey="forecastUpper" name="Forecast upper" stroke="#d8b06a" strokeWidth={1.2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function AccelerationChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="year" {...commonAxisProps()} />
        <YAxis {...commonAxisProps()} tickFormatter={numberTick} />
        <Tooltip content={<ChartTooltip formatter={(value) => Number(value).toFixed(1)} />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area type="monotone" dataKey="realIndex" name="Real index" stroke={COLORS.accent} fill="rgba(22,94,53,0.18)" strokeWidth={2.5} />
        <Line type="monotone" dataKey="nominalIndex" name="Nominal index" stroke={COLORS.blue} strokeWidth={2} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function SupplierBreakdownChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" horizontal={false} />
        <XAxis type="number" {...commonAxisProps()} tickFormatter={shortPercent} />
        <YAxis dataKey="country" type="category" width={90} {...commonAxisProps()} />
        <Tooltip content={<ChartTooltip formatter={(value, _name, payload) => `${shortPercent(value)} | ${shortBillions(payload.value)} | Risk ${payload.risk}/10`} />} />
        <Bar dataKey="share" name="Market share" radius={[8, 8, 8, 8]}>
          {data.map((entry) => (
            <Cell
              key={entry.country}
              fill={
                entry.level === "Critical"
                  ? COLORS.red
                  : entry.level === "High"
                    ? COLORS.amber
                    : entry.level === "Moderate"
                      ? COLORS.blue
                      : COLORS.success
              }
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function ShareTrendChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="year" {...commonAxisProps()} />
        <YAxis {...commonAxisProps()} tickFormatter={shortPercent} domain={[0, 100]} />
        <Tooltip content={<ChartTooltip formatter={shortPercent} />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area type="monotone" dataKey="chinaShare" name="China share" stroke={COLORS.red} fill="rgba(159,37,37,0.18)" strokeWidth={2.4} />
        <Area type="monotone" dataKey="nonChinaShare" name="Non-China share" stroke={COLORS.accent} fill="rgba(22,94,53,0.08)" strokeWidth={1.8} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function RiskScatterChart({ data }) {
  const preBreak = data.filter((item) => item.period === "1995-2017");
  const postBreak = data.filter((item) => item.period !== "1995-2017");

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" />
        <XAxis type="number" dataKey="chinaShare" name="China share" {...commonAxisProps()} tickFormatter={shortPercent} />
        <YAxis type="number" dataKey="hhiX100" name="HHI x100" {...commonAxisProps()} tickFormatter={numberTick} />
        <ZAxis type="number" dataKey="nominalBill" range={[60, 320]} />
        <Tooltip content={<ChartTooltip formatter={(value, _name, payload) => `${Number(value).toFixed(1)} | Year ${payload.year} | ${shortBillions(payload.nominalBill)}`} />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Scatter name="1995-2017" data={preBreak} fill={COLORS.blue} fillOpacity={0.65} />
        <Scatter name="2018-2024" data={postBreak} fill={COLORS.red} fillOpacity={0.7} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

function ProductMixChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="year" {...commonAxisProps()} />
        <YAxis yAxisId="left" {...commonAxisProps()} tickFormatter={shortBillions} />
        <YAxis yAxisId="right" orientation="right" {...commonAxisProps()} tickFormatter={shortPercent} domain={[0, 100]} />
        <Tooltip content={<ChartTooltip formatter={(value, name) => (name === "HS 8542 share" ? shortPercent(value) : shortBillions(value))} />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar yAxisId="left" dataKey="hs8542Bill" name="HS 8542 bill" fill={COLORS.accent} radius={[4, 4, 0, 0]} />
        <Bar yAxisId="left" dataKey="hs3818Bill" name="HS 3818 bill" fill={COLORS.amber} radius={[4, 4, 0, 0]} />
        <Line yAxisId="right" type="monotone" dataKey="hs8542Share" name="HS 8542 share" stroke={COLORS.blue} strokeWidth={2.2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function GrowthChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="year" {...commonAxisProps()} />
        <YAxis {...commonAxisProps()} tickFormatter={shortPercent} />
        <Tooltip content={<ChartTooltip formatter={shortPercent} />} />
        <Bar dataKey="yoyReal" name="Real growth" radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.year} fill={entry.yoyReal >= 0 ? COLORS.success : COLORS.red} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function VolatilityChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="year" {...commonAxisProps()} />
        <YAxis {...commonAxisProps()} tickFormatter={numberTick} />
        <Tooltip content={<ChartTooltip formatter={(value) => Number(value).toFixed(1)} />} />
        <Area type="monotone" dataKey="volatility" name="Rolling volatility" stroke={COLORS.amber} fill="rgba(184,110,11,0.16)" strokeWidth={2.3} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function YearContextChart({ data, selectedYear, compareYear }) {
  const selectedPoint = data.find((row) => row.year === selectedYear);
  const comparePoint = compareYear ? data.find((row) => row.year === compareYear) : null;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="year" {...commonAxisProps()} />
        <YAxis {...commonAxisProps()} tickFormatter={shortBillions} />
        <Tooltip content={<ChartTooltip formatter={shortBillions} />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {compareYear ? (
          <ReferenceLine
            x={compareYear}
            stroke={COLORS.amber}
            strokeDasharray="4 4"
            label={{ value: String(compareYear), position: "insideTopLeft", fill: COLORS.amber, fontSize: 11 }}
          />
        ) : null}
        <ReferenceLine
          x={selectedYear}
          stroke={COLORS.red}
          strokeDasharray="4 4"
          label={{ value: String(selectedYear), position: "insideTopRight", fill: COLORS.red, fontSize: 11 }}
        />
        {comparePoint ? (
          <>
            <ReferenceDot
              x={compareYear}
              y={comparePoint.real}
              r={5}
              fill="#fff7ec"
              stroke={COLORS.amber}
              strokeWidth={2}
              ifOverflow="visible"
            />
            <ReferenceDot
              x={compareYear}
              y={comparePoint.nominal}
              r={5}
              fill="#fff7ec"
              stroke={COLORS.amber}
              strokeWidth={2}
              ifOverflow="visible"
            />
          </>
        ) : null}
        {selectedPoint ? (
          <>
            <ReferenceDot
              x={selectedYear}
              y={selectedPoint.real}
              r={5.5}
              fill="#fff"
              stroke={COLORS.red}
              strokeWidth={2.5}
              ifOverflow="visible"
            />
            <ReferenceDot
              x={selectedYear}
              y={selectedPoint.nominal}
              r={5.5}
              fill="#fff"
              stroke={COLORS.red}
              strokeWidth={2.5}
              ifOverflow="visible"
            />
          </>
        ) : null}
        <Line type="monotone" dataKey="real" name="Real imports" stroke={COLORS.accent} strokeWidth={2.5} dot={false} />
        <Line type="monotone" dataKey="nominal" name="Nominal imports" stroke={COLORS.accent2} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function SubstitutionChart({ data, formatter }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="year" {...commonAxisProps()} />
        <YAxis {...commonAxisProps()} tickFormatter={formatter} />
        <Tooltip content={<ChartTooltip formatter={formatter} />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="historical" name="Historical" stroke={COLORS.accent} strokeWidth={2.2} dot={{ r: 2.5 }} />
        <Line type="monotone" dataKey="bau" name="BAU forecast" stroke={COLORS.amber} strokeWidth={2} strokeDasharray="6 4" dot={{ r: 4 }} />
        <Line type="monotone" dataKey="actual" name="Actual" stroke={COLORS.red} strokeWidth={0} dot={{ r: 6, fill: COLORS.red }} activeDot={{ r: 7 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function RiskCorridorChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="year" {...commonAxisProps()} />
        <YAxis yAxisId="left" {...commonAxisProps()} tickFormatter={shortPercent} domain={[0, 60]} />
        <YAxis yAxisId="right" orientation="right" {...commonAxisProps()} tickFormatter={numberTick} domain={[0, 35]} />
        <Tooltip content={<ChartTooltip formatter={(value, name) => (name === "HHI x100" ? numberTick(value) : shortPercent(value))} />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area yAxisId="left" type="monotone" dataKey="chinaShare" name="China share" stroke={COLORS.red} fill="rgba(159,37,37,0.14)" strokeWidth={2.4} />
        <Line yAxisId="right" type="monotone" dataKey="hhiX100" name="HHI x100" stroke={COLORS.amber} strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function RiskBarChart({ data, dataKey, name, domain }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="year" {...commonAxisProps()} />
        <YAxis {...commonAxisProps()} domain={domain} tickFormatter={name === "Risk score" ? numberTick : numberTick} />
        <Tooltip content={<ChartTooltip formatter={(value) => (name === "Risk score" ? Number(value).toFixed(1) : Number(value).toFixed(3))} />} />
        <Bar dataKey={dataKey} name={name} radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell
              key={entry.year}
              fill={
                name === "Risk score"
                  ? entry[dataKey] >= 7
                    ? COLORS.red
                    : entry[dataKey] >= 5
                      ? COLORS.amber
                      : COLORS.success
                  : entry[dataKey] >= 0.25
                    ? COLORS.red
                    : entry[dataKey] >= 0.15
                      ? COLORS.amber
                      : COLORS.success
              }
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function YearImportsChart({ detail, compareDetail, selectedYear, compareYear }) {
  if (compareDetail && compareYear) {
    const focusLabel = String(selectedYear ?? detail.year);
    const compareLabel = String(compareYear ?? compareDetail.year);
    const data = [
      { label: "Nominal imports", focus: detail.nominalBill, compare: compareDetail.nominalBill },
      { label: "Real imports", focus: detail.realBill, compare: compareDetail.realBill }
    ];

    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
          <XAxis dataKey="label" {...commonAxisProps()} />
          <YAxis {...commonAxisProps()} tickFormatter={shortBillions} />
          <Tooltip content={<ChartTooltip formatter={shortBillions} />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="compare" name={compareLabel} fill={COLORS.amber} radius={[6, 6, 0, 0]} />
          <Bar dataKey="focus" name={focusLabel} fill={COLORS.accent2} radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  const data = [
    { label: "Nominal imports", value: detail.nominalBill },
    { label: "Real imports", value: detail.realBill }
  ];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="label" {...commonAxisProps()} />
        <YAxis {...commonAxisProps()} tickFormatter={shortBillions} />
        <Tooltip content={<ChartTooltip formatter={shortBillions} />} />
        <Bar dataKey="value" name="Value" fill={COLORS.accent} radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function YearMixChart({ detail, compareDetail, selectedYear, compareYear }) {
  if (compareDetail && compareYear) {
    const focusLabel = String(selectedYear ?? detail.year);
    const compareLabel = String(compareYear ?? compareDetail.year);
    const data = [
      { label: "HS 8542 share", focus: detail.hs8542Share, compare: compareDetail.hs8542Share },
      { label: "HS 3818 share", focus: detail.hs3818Share, compare: compareDetail.hs3818Share }
    ];

    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 10, left: 8, bottom: 0 }}>
          <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" horizontal={false} />
          <XAxis type="number" {...commonAxisProps()} tickFormatter={shortPercent} domain={[0, 100]} />
          <YAxis dataKey="label" type="category" width={92} {...commonAxisProps()} />
          <Tooltip content={<ChartTooltip formatter={shortPercent} />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="compare" name={compareLabel} fill={COLORS.amber} radius={[6, 6, 6, 6]} />
          <Bar dataKey="focus" name={focusLabel} fill={COLORS.accent2} radius={[6, 6, 6, 6]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  const data = [
    { name: "HS 8542", value: detail.hs8542Bill, fill: COLORS.accent },
    { name: "HS 3818", value: detail.hs3818Bill, fill: COLORS.amber }
  ];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Tooltip content={<ChartTooltip formatter={shortBillions} />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={52} outerRadius={86} paddingAngle={3}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.fill} />
          ))}
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  );
}

export function YearRiskChart({ detail, compareDetail, selectedYear, compareYear }) {
  if (compareDetail && compareYear) {
    const focusLabel = String(selectedYear ?? detail.year);
    const compareLabel = String(compareYear ?? compareDetail.year);
    const data = [
      { label: "China share", focus: detail.chinaShare, compare: compareDetail.chinaShare },
      { label: "Non-China", focus: detail.nonChinaShare, compare: compareDetail.nonChinaShare },
      { label: "HHI x100", focus: detail.hhiX100, compare: compareDetail.hhiX100 }
    ];

    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
          <XAxis dataKey="label" {...commonAxisProps()} />
          <YAxis {...commonAxisProps()} domain={[0, 100]} tickFormatter={numberTick} />
          <Tooltip content={<ChartTooltip formatter={numberTick} />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="compare" name={compareLabel} fill={COLORS.amber} radius={[6, 6, 0, 0]} />
          <Bar dataKey="focus" name={focusLabel} fill={COLORS.accent2} radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  const data = [
    { label: "China share", value: detail.chinaShare, fill: COLORS.red },
    { label: "Non-China", value: detail.nonChinaShare, fill: COLORS.accent },
    { label: "HHI x100", value: detail.hhiX100, fill: COLORS.amber }
  ];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis dataKey="label" {...commonAxisProps()} />
        <YAxis {...commonAxisProps()} domain={[0, 100]} tickFormatter={numberTick} />
        <Tooltip content={<ChartTooltip formatter={numberTick} />} />
        <Bar dataKey="value" name="Selected year" radius={[8, 8, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.label} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
