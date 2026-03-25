# India Semiconductor Import Dependence: Trade Trends, Risks, and Policy Implications

## 1. Executive Summary

India remains highly dependent on imported semiconductors, and that dependence increased rather than declined over the 1995-2024 period covered by the BACI-style dataset. India's semiconductor import bill rose from **$0.24 billion nominal in 1995** to **$23.05 billion nominal in 2024**, and from **$0.87 billion to $14.60 billion in real 2015 USD terms**. That implies roughly **10.2% annual real growth** over three decades.

The import basket is overwhelmingly dominated by **HS 8542 integrated circuits**, which accounted for **99.18% of the tracked import bill in 2024**. By contrast, **HS 3818 semiconductor materials** remained very small at **0.82%**. This matters because it suggests India is still importing mostly finished or near-finished chip value, not large volumes of upstream semiconductor materials.

Supplier dependence has also intensified. In 2024, **China supplied 45.83%** of tracked semiconductor imports, while **China, Taiwan, and South Korea together supplied 86.56%**. The supplier concentration index (`supplier_hhi`) rose from **0.051 in 1995** to **0.291 in 2024**, showing that even though India buys from more countries than before, more of the value is now concentrated in a small number of Asian hubs.

The data do **not** show clear historical evidence of import substitution through 2024. A genuine substitution signal would require imported finished chips to flatten or fall while semiconductor materials rise. That did not happen. Materials imports rose in some years, especially in 2023, but finished-chip imports also rose strongly and reached new highs in 2024. The policy conclusion is that India's semiconductor strategy is promising but still in the build-out phase; up to 2024 it had **not yet materially reduced import dependence in observed trade data**.

## 2. Business Problem

Semiconductors are now foundational to almost every growth sector the Government of India cares about: mobile phones, telecom equipment, automobiles, power electronics, defense electronics, industrial automation, digital infrastructure, and AI-enabled devices. If India wants to deepen manufacturing, move up global value chains, and protect macroeconomic resilience, it cannot ignore semiconductor import dependence.

Why this matters for India:

- A rising semiconductor import bill increases pressure on the import side of the electronics trade balance and adds demand for foreign exchange.
- Heavy import dependence can slow domestic value addition because higher-value stages of the chain remain offshore.
- Supply disruptions can quickly transmit into domestic manufacturing, exports, inflation, and employment.
- Semiconductor supply chains are geographically concentrated, which makes dependency not just commercial but strategic.

The main risks are:

- **Dependency risk:** India's electronics growth can translate directly into a larger import bill if local semiconductor capacity does not keep pace.
- **Supply-chain risk:** Delays in one foreign node can affect multiple downstream Indian industries simultaneously.
- **Geopolitical risk:** Supplier concentration in East Asia increases vulnerability to export controls, shipping disruptions, or regional conflict.
- **Industrial policy risk:** If India expands final electronics assembly faster than semiconductor capability, import dependence can deepen even while manufacturing headlines look strong.

For a Finance Minister, the business problem is therefore not simply "How much are we importing?" It is "Are we building domestic capacity fast enough to stop downstream growth from continuously increasing upstream strategic dependence?"

## 3. Dataset Understanding

### What is the BACI dataset?

The report uses a **BACI-style trade dataset**, based on CEPII's BACI database of bilateral trade flows. BACI is a harmonized trade dataset built from international customs records and reported at detailed product level, including trade value and, when available, quantities. In practical terms, it is well suited for answering policy questions such as who supplies India, how much India imports, and how the mix changes over time. Official BACI reference: [CEPII BACI database](https://www.cepii.fr/ANGLAISGRAPH/bdd/baci.htm).

### Country codes

- `699` = **India** in this filtered extract.
- `exporter_country_code` identifies the foreign supplier.
- `importer_country_code` is `699` in the raw file because all rows are filtered to India's imports.

### HS codes in scope

- **HS 8542**: Electronic integrated circuits. In business terms, this is the finished-chip category and represents the overwhelming majority of India's tracked semiconductor import value.
- **HS 3818**: Chemical elements and compounds doped for electronics use, including semiconductor materials such as doped silicon wafers and related inputs. In business terms, this is an upstream materials category rather than a finished-chip category.

### Files used in this project

- `data/raw/india_imports_8542_3818_filtered.csv`: Raw filtered BACI rows for India, HS 8542, and HS 3818.
- `data/processed/india_semiconductor_integrated_annual.csv`: Main annual policy dataset for 1995-2024.
- `data/processed/india_semiconductor_country_year_breakdown.csv`: Supplier-country view used for market share and concentration.
- `data/processed/india_semiconductor_integrated_annual_enriched.csv`: Modeling-ready version of the annual file with lags, logs, and rolling features.
- `data/synthetic/actual_imports_2025_2026.csv`: A synthetic forward-looking scenario used in the project to demonstrate substitution logic. It is **not** historical evidence and is excluded from the historical verdict in this report.

### Raw file columns

| Column | Meaning |
| --- | --- |
| `year` | Calendar year of the import flow. |
| `exporter_country_code` | Numeric BACI-style code for the exporting country. |
| `importer_country_code` | Numeric BACI-style code for the importer; `699` means India. |
| `hs_product_code` | Product code at detailed HS level. |
| `hs_chapter` | Broad HS chapter used in this project, mainly `8542` or `3818`. |
| `hs_description` | Plain-language description of the product group. |
| `trade_value_1000usd` | Trade value in thousands of US dollars. |
| `trade_value_usd` | Trade value in US dollars. |
| `quantity_metric_tons` | Reported quantity in metric tons when available. |

### Annual integrated file columns

| Column | Meaning |
| --- | --- |
| `year` | Calendar year. |
| `importer_country` | Name of the importer, here India. |
| `importer_baci_code` | BACI-style numeric code for India, `699`. |
| `import_value_usd_billions` | Total imports in current US dollar billions. |
| `real_value_2015usd_billions` | Total imports deflated to 2015 US dollars, in billions. |
| `total_import_value_usd` | Total imports in current US dollars. |
| `real_import_value_2015usd` | Total imports deflated to 2015 US dollars. |
| `hs8542_import_usd` | Import value of integrated circuits. |
| `hs8542_share_pct` | Share of HS 8542 in total tracked imports. |
| `hs3818_import_usd` | Import value of semiconductor materials. |
| `hs3818_share_pct` | Share of HS 3818 in total tracked imports. |
| `total_quantity_mt` | Aggregate reported quantity in metric tons. |
| `yoy_nominal_growth_pct` | Year-on-year growth in current-dollar imports. |
| `yoy_real_growth_pct` | Year-on-year growth in inflation-adjusted imports. |
| `num_exporting_countries` | Number of supplier countries recorded in that year. |
| `num_hs6_products` | Number of detailed product lines present in that year within scope. |
| `num_transactions` | Count of trade rows used in the yearly aggregate. |
| `top_exporter_name` | Largest supplier in that year by value. |
| `top3_supplier_share_pct` | Combined share of the top three suppliers by value. |
| `china_import_usd` | Imports sourced from China. |
| `china_share_pct` | China's share of total imports. |
| `supplier_hhi` | Herfindahl-Hirschman Index of supplier concentration. Higher means more concentration. |
| `gdp_deflator_2015_100` | Deflator index used to convert current values to 2015 dollars. |
| `dummy_post_2018_inflection` | Indicator for the post-2018 higher-growth regime. |
| `dummy_covid_shock_2020` | Indicator for 2020 pandemic disruption. |
| `dummy_global_chip_shortage_2021` | Indicator for the 2021 global shortage period. |
| `dummy_pli_scheme_launch` | Indicator capturing the policy period after launch of semiconductor-related incentives. |
| `dummy_micron_mou_2023` | Indicator for the Micron project period in 2023 onward. |
| `dummy_tata_fab_groundbreaking` | Indicator for Tata fab investment timing. |
| `dummy_india_semicon_mission` | Indicator for India Semiconductor Mission era. |
| `dgft_monthly_available` | Flag showing whether higher-frequency government data are available. |
| `hs8486_equip_import_usd_placeholder` | Placeholder for semiconductor equipment imports, not populated here. |
| `domestic_production_volume_placeholder` | Placeholder for domestic production data, not populated here. |
| `data_source` | Source label for the trade data. |
| `deflator_source` | Source label for the deflator series. |

### Country-year breakdown file columns

| Column | Meaning |
| --- | --- |
| `year` | Calendar year. |
| `exporter_country_code` | Numeric code for the supplying country. |
| `exporter_name` | Country name used in the report. |
| `import_value_usd` | Value imported from that exporter. |
| `quantity_mt` | Quantity imported from that exporter in metric tons. |
| `num_products` | Number of distinct in-scope product lines sourced from that exporter. |
| `year_total_usd` | India's total tracked semiconductor imports for that year. |
| `market_share_pct` | Supplier share in that year's total. |
| `data_source` | Source label. |
| `importer` | Importer label, here India. |
| `hs_scope` | The product scope covered by the file. |

### Enriched file additions used for modeling

| Column | Meaning |
| --- | --- |
| `log_real_import` | Natural log of real imports. |
| `log_diff` | First difference of the log series. |
| `first_diff_real` | First difference of real imports in level terms. |
| `rolling3_real` | Three-year rolling average of real imports. |
| `lag1_real` | One-year lag of real imports. |
| `lag2_real` | Two-year lag of real imports. |
| `china_share_squared` | China's market share squared, used as a nonlinear risk feature. |
| `hhi_diff` | Year-on-year change in supplier concentration. |

## 4. Methodology

The analysis combines descriptive trade analytics with light, policy-oriented time-series modeling.

### What was done

1. Annual imports were reviewed from **1995 to 2024** in both nominal and inflation-adjusted terms.
2. Product mix was separated into **finished chips (HS 8542)** and **semiconductor materials (HS 3818)**.
3. Supplier-country shares were analyzed to identify the largest external dependencies.
4. Concentration was measured using market shares and the Herfindahl-Hirschman Index.
5. Growth rates and structural changes were evaluated to identify regime shifts.
6. Existing project outputs for stationarity tests, structural-break testing, ARIMA, and ARIMAX forecasting were incorporated to describe the broader analytical framework.

### Why this methodology was chosen

- **Finance-ministry relevance:** Total import value, supplier concentration, and product mix are the most decision-useful indicators for fiscal, industrial, and strategic policy.
- **Inflation control:** Real 2015-dollar values are more reliable for long-run comparison than nominal values alone.
- **Business logic:** The distinction between HS 8542 and HS 3818 is economically meaningful because it separates finished chips from upstream materials.
- **Risk logic:** Market-share and HHI measures help distinguish "many suppliers on paper" from true value diversification.
- **Policy logic:** Structural-break and ARIMAX analysis are useful because semiconductor trade is shaped not only by past momentum but also by policy shifts and global shocks.

### Assumptions and caveats

- This is an **import-side** dataset. It does not directly measure India's total semiconductor consumption, exports, or domestic output.
- Therefore, "dependency" is inferred from persistent import growth and the absence of visible substitution, not from a complete self-sufficiency ratio.
- `quantity_metric_tons` is informative but should be treated cautiously because chip value density varies widely across products.
- The forward-looking file `actual_imports_2025_2026.csv` is synthetic and is **not** used as historical proof.
- Where this report explains the probable causes of a trend, that interpretation is an **economic inference from the data plus known industry events**, not a claim of strict causal proof.

## 5. Exploratory Data Analysis

All monetary comparisons below are stated in **real 2015 USD** unless otherwise noted.

### Chart 1. Total imports over time

![Chart 1: Total imports over time](../charts/minister_chart_1_total_imports_real.png)

- **What the chart shows:** India's semiconductor imports rose from **$0.87 billion in 1995** to **$14.60 billion in 2024** in real terms. The long-run path is upward, but with visible setbacks around **1996**, **2008**, **2013-2015**, and **2020**, followed by a sharp acceleration after **2018**.
- **Why the trend increases or decreases:** The broad rise reflects India's expanding electronics consumption and assembly base. The declines are consistent with cyclical slowdowns, weaker demand, or external shocks rather than a sustained fall in semiconductor need.
- **Economic reasoning:** When downstream industries such as consumer electronics, telecom, autos, and industrial systems grow faster than domestic chip-making capacity, the import bill rises almost mechanically.
- **Real-world causes:** The **2008** decline aligns with the global financial crisis, the **2020** dip aligns with pandemic disruption, and the post-**2018** acceleration is consistent with stronger domestic electronics demand and deeper integration into Asian electronics supply chains. The repo's structural-break test also confirms **2018** as a statistically significant turning point (`F=242.692`, `p<0.001`).

### Chart 2. Imports by product type (HS 3818 vs HS 8542)

![Chart 2: Imports by product type](../charts/minister_chart_2_product_mix.png)

- **What the chart shows:** Nearly the entire import bill consists of **HS 8542 integrated circuits**. Across the full sample, **97.68%** of cumulative import value came from HS 8542 and only **2.32%** from HS 3818. In 2024, the split was **99.18% HS 8542** and **0.82% HS 3818**.
- **Why the trend increases or decreases:** Materials imports do rise intermittently, especially in **2023**, but they remain far too small to change the overall composition of the basket.
- **Economic reasoning:** This is the signature of a country that primarily imports the higher-value semiconductor content embedded in finished or near-finished chips, while only a limited share of the upstream materials chain is visible domestically.
- **Real-world causes:** India's semiconductor ecosystem has historically been stronger in design and downstream electronics assembly than in wafer fabrication, packaging, or materials processing. The 2023 rise in HS 3818 likely reflects early ecosystem preparation or stocking, but because HS 8542 also surged, it does **not** yet indicate substitution.

### Chart 3. Top exporting countries to India

![Chart 3: Top exporting countries to India](../charts/minister_chart_3_top_exporters_2024.png)

- **What the chart shows:** In **2024**, India sourced most tracked semiconductor imports from **China (45.8%)**, **Taiwan (25.7%)**, and **South Korea (15.0%)**. Japan, Malaysia, and Singapore were much smaller.
- **Why the trend increases or decreases:** India increasingly sources from the countries that dominate the global semiconductor ecosystem, especially for scale, process know-how, and advanced product availability.
- **Economic reasoning:** Semiconductor manufacturing benefits from extreme economies of scale, ecosystem depth, and decades of accumulated capability. Buyers therefore concentrate sourcing in the global hubs that can supply large volumes reliably and at competitive cost.
- **Real-world causes:** East Asia remains the center of global semiconductor fabrication and packaging. India's 2024 sourcing pattern mirrors that global reality. For policy, the key message is that India's exposure is no longer diffuse; it is heavily tied to a narrow set of leading Asian hubs.

### Chart 4. Market share trends

![Chart 4: Market share trends](../charts/minister_chart_4_market_share_trends.png)

- **What the chart shows:** China's share rose from **0.78% in 1995** to **45.83% in 2024**. Taiwan's share rose to **25.68%** by 2024, while South Korea remained consistently important. Singapore was dominant in earlier years but declined sharply, and Hong Kong saw a temporary spike from **2018 to 2022** before collapsing in **2023-2024**.
- **Why the trend increases or decreases:** Supplier shares change when India's demand mix changes, when procurement channels are reorganized, or when firms move from intermediary trading hubs to direct sourcing from fabrication centers.
- **Economic reasoning:** More sophisticated and larger-scale demand tends to favor the world's most specialized semiconductor producers. That naturally pulls trade toward Taiwan, South Korea, and China and away from more diversified or intermediary suppliers.
- **Real-world causes:** The rise of China, Taiwan, and South Korea is consistent with the global concentration of foundries, memory production, and packaging ecosystems. The fall of Singapore and Hong Kong is best read as an **inference** of supply-chain rerouting and channel normalization rather than direct evidence of lower Asian exposure. In other words, the supplier names changed, but the dependence on East Asian hubs intensified.

### Chart 5. Growth rate over time

![Chart 5: Growth rate over time](../charts/minister_chart_5_growth_rate.png)

- **What the chart shows:** Import growth is volatile but trending higher in the post-2018 period. Real growth peaked at **150.83% in 2018**, fell in **2020**, then rebounded strongly in **2021-2024**.
- **Why the trend increases or decreases:** Semiconductor demand is tied to the electronics cycle, but it also has a strong structural trend because chips are spreading across more sectors over time.
- **Economic reasoning:** The volatility reflects two forces at once: cyclical shocks change timing, while structural digitalization keeps the medium-term direction upward. That is why downturns tend to be temporary rather than permanent.
- **Real-world causes:** The **2020** contraction reflects pandemic disruption; the **2021-2022** rebound reflects recovery plus the global chip shortage period; the continued growth in **2023-2024** reflects persistent domestic electronics demand and the absence of large-scale import replacement. Average annual real growth was about **10.0% before 2018** and **34.9% from 2018 onward**.

## 6. Deep Insights

### Is India dependent on imports?

**Yes. Strongly.**

The evidence is straightforward:

- Real imports rose more than sixteen-fold between 1995 and 2024.
- The basket is dominated by finished chips, not upstream materials.
- There is no populated domestic production series in the core dataset to offset this import growth.
- The largest suppliers are a small set of external semiconductor powers.

This does not prove India imports 100% of its semiconductor needs, but it clearly shows that the country's electronics expansion has been accompanied by a much larger external semiconductor bill.

### Is dependency increasing or decreasing?

**Increasing.**

The most important signs are:

- **Import scale:** real imports grew at about **10.2% CAGR** over the full sample.
- **Post-2018 acceleration:** real imports grew at about **13.9% CAGR from 2018 to 2024**.
- **Supplier concentration:** HHI increased from **0.051** to **0.291**.
- **China exposure:** China's share rose from **0.78%** to **45.83%**.
- **Regional concentration:** using an analyst-defined East Asia supplier grouping, the region's share rose from **44.38% in 1995** to **96.12% in 2024**.

An important nuance is that the number of suppliers increased from **45** to **94**, yet concentration still rose. That means diversification expanded in a superficial sense, but the bulk of value became more concentrated.

### Is there evidence of substitution, meaning domestic production replacing imports?

**Not in the historical data through 2024.**

The project uses a sensible business test for substitution:

- If domestic semiconductor activity is replacing imported finished chips, imports of **HS 8542** should weaken.
- At the same time, imports of **HS 3818** and related upstream inputs may rise because domestic plants still need raw materials.

That combined pattern does **not** appear in the observed history:

- **2023:** HS 3818 rose **83.2%**, but HS 8542 also rose **14.3%**.
- **2024:** HS 3818 fell **43.2%**, while HS 8542 rose another **22.4%** to a record high.

So the correct conclusion is:

- There may be **early ecosystem formation**.
- There is **no historical proof of substitution yet**.

### Why has substitution not appeared yet?

The most likely reasons are:

- Semiconductor projects have long gestation periods; approvals do not translate immediately into lower imports.
- India has been expanding downstream electronics demand faster than semiconductor manufacturing capability.
- Back-end capacity such as ATMP/OSAT can reduce some finished-chip imports over time, but large-scale substitution requires a broader ecosystem: packaging, testing, specialty gases, chemicals, capital equipment, power reliability, water, talent, and supplier depth.
- Even if new plants are underway, their effect often appears first as **additional** imports of machinery and inputs, not immediate reductions in finished-chip imports.

In short, the pipeline may be improving, but the **1995-2024 data still describe an import-dependent system**.

## 7. Economic & Policy Interpretation

### Trade deficit implications

This project does not include exports, so it cannot calculate India's semiconductor trade deficit directly. But the import-side implication is still clear: unless matched by semiconductor exports or domestic substitution, a rising import bill worsens the external balance of the electronics ecosystem. That raises foreign-exchange exposure and makes domestic manufacturing margins more sensitive to global semiconductor prices and exchange-rate changes.

### Industrial policy gaps

The data suggest three core gaps:

- **Depth gap:** India has expanded electronics demand faster than semiconductor manufacturing depth.
- **Upstream gap:** HS 3818 remains tiny, showing weak visible integration into upstream semiconductor materials.
- **Concentration gap:** Import sourcing is becoming more concentrated, not less, despite a larger supplier count.

### Strategic risks

- Dependence is concentrated in geographies that are strategically sensitive for global technology supply chains.
- A disruption involving China, Taiwan, or the Korea-Taiwan manufacturing corridor would transmit quickly into Indian manufacturing.
- The risk is not only a shortage risk. It is also a bargaining-power risk: countries with concentrated supply have more leverage over price, delivery, and technology access.

### Policy context

The historical data end in **2024**, but the policy backdrop matters. Official Government of India releases confirm that the **Programme for Development of Semiconductors and Display Manufacturing Ecosystem in India** was approved on **15 December 2021** and notified on **21 December 2021**; Micron's Sanand unit was approved in **June 2023**; three more semiconductor units were approved on **29 February 2024**; and another unit was approved on **2 September 2024**. A PIB explainer posted on **1 September 2025** states that India had **10 approved semiconductor projects across six states**, with several still in pilot, construction, or ramp-up stages. These developments are strategically important, but they are mostly too recent to overturn the import-dependence picture visible in the 1995-2024 trade data. Relevant official links: [PIB note on the 2021 programme](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1883839), [PIB release noting the three approvals received on 29 February 2024](https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2014331), [PIB on the 2 September 2024 approval](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2050859&noshow=1), [PIB explainer dated 1 September 2025](https://www.pib.gov.in/PressNoteDetails.aspx?NoteId=155130&ModuleId=3&reg=3&lang=2), and [PIB note confirming Micron's June 2023 approval](https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=1983128).

### Recommendations

#### Short-term actions

- **Build a semiconductor import risk dashboard for the fiscal system.** Track monthly customs and market-share changes, not only annual values.
- **Set supplier-diversification targets.** Reducing concentration is valuable even before full domestic substitution is achieved.
- **Prioritize ATMP/OSAT and specialty materials where entry barriers are lower than for frontier fabs.**
- **Link electronics manufacturing incentives to realistic localization milestones.** The goal should be gradual deepening of value addition, not only assembly volume.
- **Use strategic procurement and diplomacy with Taiwan, South Korea, Japan, and trusted partners** to reduce disruption risk.

#### Long-term actions

- **Develop the full ecosystem, not only anchor plants.** Fabs and OSAT units require gases, chemicals, substrates, equipment maintenance, logistics, utilities, and skilled labor.
- **Focus on commercially sensible niches first.** Mature-node, automotive, industrial, power electronics, and compound semiconductors may offer a more practical path than immediate competition at the frontier.
- **Invest in infrastructure reliability.** Semiconductor production depends on uninterrupted power, high-quality water, cleanroom systems, and logistics precision.
- **Create a domestic demand-to-supply bridge.** Use public and private procurement in autos, telecom, energy, and defense to support domestic semiconductor manufacturing once capacity becomes credible.
- **Treat semiconductor capability as strategic economic infrastructure.** The payoff is not only industrial output; it is resilience, bargaining power, and a stronger long-run external account.

## 8. Modeling & Analysis

The broader project uses several light and interpretable models. The point is not to produce abstract mathematics, but to improve policy judgment.

### Models used

- **Trend analysis:** Long-run nominal and real import trajectories.
- **Growth analysis:** Year-on-year growth and rolling averages to show volatility and acceleration.
- **Market-share analysis:** Supplier shares to identify dependency structure.
- **Concentration analysis:** HHI to measure whether supplier exposure is becoming safer or riskier.
- **Structural-break testing:** The project runs a Chow test and finds a confirmed break in **2018**.
- **ARIMA:** A baseline forecast using the historical import series alone.
- **ARIMAX:** An extended forecast that adds policy and shock indicators such as the post-2018 inflection, COVID shock, global chip shortage, PLI-era effects, and the Micron period.
- **Mix-shift logic:** A business-rule test for substitution that looks for falling HS 8542 imports alongside rising HS 3818 imports.

### Why these models were chosen

- They match the policy question. The issue is not high-frequency trading or machine-learning classification; it is whether import dependence is rising, breaking, or beginning to shift.
- They are transparent. A minister can understand growth rates, market shares, and concentration much more easily than a black-box model.
- They combine business reasoning with statistical discipline. Structural breaks and inflation adjustments are essential in a series that changed sharply after 2018.

### What the models revealed

- The level series is non-stationary, which means simple level extrapolation is unreliable. The project's diagnostics show the log-differenced real series is stationary.
- The **2018 break is real**, not just visual. That supports treating the recent period as a distinct regime.
- The project's preferred forecasting model is **ARIMAX(1,1,0)**. Its evaluation report shows an **AIC of 16.00** versus **21.25** for the plain ARIMA baseline, and a **2023-2024 holdout MAPE of 12.92%**.
- However, the rolling backtest also shows that uncertainty remains meaningful. ARIMAX improves on plain ARIMA, but it should still be treated as a **scenario baseline**, not a precise oracle.
- The BAU forecast in the repo points to real imports around **$13.9-$14.2 billion** in 2025-2027, which implies that without strong substitution India remains on a high-import plateau.

### Interpretation for policymakers

The modeling result is not that India is "locked in forever." It is that the historical pattern is strong enough that import dependence will persist unless policy-induced capacity becomes large enough to visibly change the trade mix. That is exactly why the mix-shift framework is useful.

One final caveat is important: the repo contains a **synthetic** 2025-2026 file that intentionally demonstrates what substitution would look like. In that synthetic scenario, the project detects substitution because finished-chip imports fall below the BAU path while materials rise above it. That is useful as a policy monitoring tool, but it is **not historical proof**.

## 9. Conclusion

The final verdict is clear: **India's semiconductor position improved in ambition, but not yet in measured import independence through 2024**. The country is importing far more semiconductors than before, sourcing them from a narrower group of foreign suppliers, and still relying overwhelmingly on finished chips rather than upstream materials.

That should not be read as policy failure. It should be read as a realistic assessment of timing. Semiconductor industrial policy works slowly. The approvals, investments, and pilot lines now underway may matter greatly in the second half of this decade. But the trade data available up to **2024** still show a country in the **capability-building stage**, not yet in the **substitution stage**.

For the Finance Minister, the actionable takeaway is: **treat semiconductors as strategic infrastructure, manage import concentration immediately, and keep financing the ecosystem long enough for recent investments to move from announcement to measurable trade impact.**
